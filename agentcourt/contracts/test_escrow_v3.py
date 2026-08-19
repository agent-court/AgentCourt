import json
import os
import pytest
from web3 import Web3
from eth_tester import EthereumTester, PyEVMBackend

@pytest.fixture
def eth_setup():
    tester = EthereumTester(PyEVMBackend())
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    accounts = w3.eth.accounts

    admin = accounts[0]
    court = accounts[1]
    client = accounts[2]
    contractor = accounts[3]
    attacker = accounts[4]

    contracts_dir = os.path.dirname(os.path.abspath(__file__))
    abi_path = os.path.join(contracts_dir, "AgentEscrowV3_abi.json")
    bin_path = os.path.join(contracts_dir, "AgentEscrowV3_bytecode.bin")

    with open(abi_path, "r") as f:
        abi = json.load(f)
    with open(bin_path, "r") as f:
        bytecode = f.read()

    ContractFactory = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = ContractFactory.constructor(admin, court).transact({"from": admin})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract = w3.eth.contract(address=receipt.contractAddress, abi=abi)

    return {
        "w3": w3,
        "tester": tester,
        "contract": contract,
        "admin": admin,
        "court": court,
        "client": client,
        "contractor": contractor,
        "attacker": attacker
    }

def test_task_creation_and_dispute(eth_setup):
    c = eth_setup["contract"]
    client = eth_setup["client"]
    contractor = eth_setup["contractor"]

    # 1. Client deposits 1 ETH to create task
    deposit = Web3.to_wei(1, "ether")
    tx = c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": deposit})
    eth_setup["w3"].eth.wait_for_transaction_receipt(tx)

    task = c.functions.tasks(1).call()
    assert task[1] == client
    assert task[2] == contractor
    assert task[3] == deposit
    assert task[6] == 1  # TaskStatus.Active

    # 2. Client raises dispute
    c.functions.raiseDispute(1, "ipfs://evidence_hash").transact({"from": client})
    task = c.functions.tasks(1).call()
    assert task[6] == 3  # TaskStatus.Disputed

def test_access_control_court_role(eth_setup):
    c = eth_setup["contract"]
    client = eth_setup["client"]
    contractor = eth_setup["contractor"]
    attacker = eth_setup["attacker"]
    court = eth_setup["court"]

    deposit = Web3.to_wei(1, "ether")
    c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": deposit})
    c.functions.raiseDispute(1, "ipfs://evidence_hash").transact({"from": client})

    # Unauthorized party tries to propose ruling -> must fail
    with pytest.raises(Exception):
        c.functions.proposeRuling(1, 8000, "ipfs://verdict_hash").transact({"from": attacker})

    # Authorized Court proposes ruling -> succeeds
    tx = c.functions.proposeRuling(1, 8000, "ipfs://verdict_hash").transact({"from": court})
    eth_setup["w3"].eth.wait_for_transaction_receipt(tx)

    task = c.functions.tasks(1).call()
    assert task[6] == 4  # TaskStatus.RulingProposed
    assert task[7] == 8000  # 80% contractor split

def test_challenge_period_and_resolution(eth_setup):
    c = eth_setup["contract"]
    w3 = eth_setup["w3"]
    tester = eth_setup["tester"]
    client = eth_setup["client"]
    contractor = eth_setup["contractor"]
    court = eth_setup["court"]

    deposit = Web3.to_wei(1, "ether")
    c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": deposit})
    c.functions.raiseDispute(1, "ipfs://evidence_hash").transact({"from": client})
    c.functions.proposeRuling(1, 7500, "ipfs://verdict_hash").transact({"from": court})

    # Premature execution during challenge window -> must fail
    with pytest.raises(Exception):
        c.functions.executeRuling(1).transact({"from": client})

    # Fast forward time past 1 hour challenge window
    tester.time_travel(int(tester.get_block_by_number("latest")["timestamp"]) + 3601)
    tester.mine_block()

    # Execute ruling: 75% contractor, 25% client refund
    tx = c.functions.executeRuling(1).transact({"from": client})
    w3.eth.wait_for_transaction_receipt(tx)

    task = c.functions.tasks(1).call()
    assert task[6] == 5  # TaskStatus.Resolved

def test_direct_completion_without_dispute(eth_setup):
    c = eth_setup["contract"]
    w3 = eth_setup["w3"]
    client = eth_setup["client"]
    contractor = eth_setup["contractor"]

    deposit = Web3.to_wei(1, "ether")
    c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": deposit})

    # Client directly marks task complete
    initial_balance = w3.eth.get_balance(contractor)
    tx = c.functions.completeTask(1).transact({"from": client})
    w3.eth.wait_for_transaction_receipt(tx)

    task = c.functions.tasks(1).call()
    assert task[6] == 2  # TaskStatus.Completed
    assert w3.eth.get_balance(contractor) == initial_balance + deposit

def test_pause_and_unpause_guards(eth_setup):
    c = eth_setup["contract"]
    admin = eth_setup["admin"]
    attacker = eth_setup["attacker"]
    contractor = eth_setup["contractor"]
    client = eth_setup["client"]

    # Non-admin cannot pause
    with pytest.raises(Exception):
        c.functions.pause().transact({"from": attacker})

    # Admin pauses contract
    c.functions.pause().transact({"from": admin})

    # Creating task while paused must fail
    with pytest.raises(Exception):
        c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": Web3.to_wei(1, "ether")})

    # Admin unpauses
    c.functions.unpause().transact({"from": admin})

def test_direct_completion_without_dispute(eth_setup):
    c = eth_setup["contract"]
    w3 = eth_setup["w3"]
    client = eth_setup["client"]
    contractor = eth_setup["contractor"]

    deposit = Web3.to_wei(1, "ether")
    c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": deposit})

    # Client directly marks task complete
    initial_balance = w3.eth.get_balance(contractor)
    tx = c.functions.completeTask(1).transact({"from": client})
    w3.eth.wait_for_transaction_receipt(tx)

    task = c.functions.tasks(1).call()
    assert task[6] == 2  # TaskStatus.Completed
    assert w3.eth.get_balance(contractor) == initial_balance + deposit

def test_pause_and_unpause_guards(eth_setup):
    c = eth_setup["contract"]
    admin = eth_setup["admin"]
    attacker = eth_setup["attacker"]
    contractor = eth_setup["contractor"]
    client = eth_setup["client"]

    # Non-admin cannot pause
    with pytest.raises(Exception):
        c.functions.pause().transact({"from": attacker})

    # Admin pauses contract
    c.functions.pause().transact({"from": admin})

    # Creating task while paused must fail
    with pytest.raises(Exception):
        c.functions.createTask(contractor, "ipfs://spec_hash", 3600).transact({"from": client, "value": Web3.to_wei(1, "ether")})

    # Admin unpauses
    c.functions.unpause().transact({"from": admin})
