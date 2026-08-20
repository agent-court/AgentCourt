import os
import time
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_standard, install_solc

load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = "https://sepolia.base.org"
CONTRACT_ADDRESS = "0x00A0197635788C997AE443C0281E86FB495CD08b"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
sender = account.address

with open("AgentEscrowV4.sol", "r") as f:
    contract_source = f.read()

install_solc("0.8.20")
compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"AgentEscrowV4.sol": {"content": contract_source}},
        "settings": {"outputSelection": {"*": {"*": ["abi"]}}},
    },
    solc_version="0.8.20",
)

contract_name = list(compiled["contracts"]["AgentEscrowV4.sol"].keys())[0]
abi = compiled["contracts"]["AgentEscrowV4.sol"][contract_name]["abi"]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

nonce = w3.eth.get_transaction_count(sender, "pending")
gas_price = int(w3.eth.gas_price * 1.25)

# 1. createJob
print(f"Creating Job (Nonce: {nonce})...")
create_tx = contract.functions.createJob(
    sender,
    sender,
    int(time.time()) + 86400,
    w3.keccak(text="Task: Automated Arbitration Test")
).build_transaction({
    "from": sender,
    "nonce": nonce,
    "gas": 300000,
    "gasPrice": gas_price,
})
signed_create = w3.eth.account.sign_transaction(create_tx, private_key=PRIVATE_KEY)
tx_create = w3.eth.send_raw_transaction(signed_create.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_create)
print(f"Job Created: {tx_create.hex()}")

# 2. fundJob
nonce += 1
print(f"Funding Job (Nonce: {nonce})...")
job_count = contract.functions.jobCount().call()
fund_tx = contract.functions.fundJob(job_count).build_transaction({
    "from": sender,
    "value": 10000,
    "nonce": nonce,
    "gas": 200000,
    "gasPrice": gas_price,
})
signed_fund = w3.eth.account.sign_transaction(fund_tx, private_key=PRIVATE_KEY)
tx_fund = w3.eth.send_raw_transaction(signed_fund.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_fund)
print(f"Job #{job_count} Funded: {tx_fund.hex()}")

# 3. submitDeliverable (triggers JobSubmitted event)
nonce += 1
print(f"Submitting Deliverable for Job #{job_count} (Nonce: {nonce})...")
submit_tx = contract.functions.submitDeliverable(
    job_count,
    w3.keccak(text="Deliverable: AI Arbitration Ready")
).build_transaction({
    "from": sender,
    "nonce": nonce,
    "gas": 200000,
    "gasPrice": gas_price,
})
signed_submit = w3.eth.account.sign_transaction(submit_tx, private_key=PRIVATE_KEY)
tx_submit = w3.eth.send_raw_transaction(signed_submit.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_submit)
print(f"Deliverable Submitted! Tx: {tx_submit.hex()}")
