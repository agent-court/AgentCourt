import os
import json
import time
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_standard, install_solc

# 1. Load Environment & Connect to Base Sepolia
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("Missing PRIVATE_KEY in .env file.")

RPC_URL = "https://sepolia.base.org"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

account = w3.eth.account.from_key(PRIVATE_KEY)
sender_address = account.address

print(f"Connected: {w3.is_connected()}")
print(f"Deployer Wallet: {sender_address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(sender_address), 'ether')} ETH")

# 2. Compile ABI
with open("AgentEscrowV4.sol", "r") as f:
    contract_source = f.read()

install_solc("0.8.20")
compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"AgentEscrowV4.sol": {"content": contract_source}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode"]}
            }
        },
    },
    solc_version="0.8.20",
)

contract_name = list(compiled["contracts"]["AgentEscrowV4.sol"].keys())[0]
abi = json.loads(compiled["contracts"]["AgentEscrowV4.sol"][contract_name]["metadata"])["output"]["abi"]

# 3. Existing Contract Address
contract_address = "0x00A0197635788C997AE443C0281E86FB495CD08b"
contract = w3.eth.contract(address=contract_address, abi=abi)
print(f"\nTarget Contract: {contract_address}")

# Get base nonce and increment sequentially
nonce = w3.eth.get_transaction_count(sender_address, "pending")

# 4. Step 1: createJob
print(f"\nStep 1: Calling createJob (Nonce: {nonce})...")
provider_address = sender_address
evaluator_address = sender_address
expiry_timestamp = int(time.time()) + 86400  # 24 hours
task_hash = w3.keccak(text="Task Details: Test Agent Court Dispute")

create_tx = contract.functions.createJob(
    provider_address,
    evaluator_address,
    expiry_timestamp,
    task_hash
).build_transaction({
    "from": sender_address,
    "nonce": nonce,
    "gas": 350000,
    "gasPrice": int(w3.eth.gas_price * 1.25),
})

signed_create = w3.eth.account.sign_transaction(create_tx, private_key=PRIVATE_KEY)
tx_create_hash = w3.eth.send_raw_transaction(signed_create.raw_transaction)
print(f"Broadcasted createJob Tx: {tx_create_hash.hex()}")
w3.eth.wait_for_transaction_receipt(tx_create_hash)
print(" Job Created Successfully!")

nonce += 1

# 5. Step 2: fundJob
print(f"\nStep 2: Calling fundJob (Nonce: {nonce})...")
fund_tx = contract.functions.fundJob(1).build_transaction({
    "from": sender_address,
    "value": 10000,
    "nonce": nonce,
    "gas": 250000,
    "gasPrice": int(w3.eth.gas_price * 1.25),
})

signed_fund = w3.eth.account.sign_transaction(fund_tx, private_key=PRIVATE_KEY)
tx_fund_hash = w3.eth.send_raw_transaction(signed_fund.raw_transaction)
print(f"Broadcasted fundJob Tx: {tx_fund_hash.hex()}")
w3.eth.wait_for_transaction_receipt(tx_fund_hash)
print(" Job Funded Successfully!")

nonce += 1

# 6. Step 3: submitDeliverable
print(f"\nStep 3: Calling submitDeliverable (Nonce: {nonce})...")
deliverable_hash = w3.keccak(text="Deliverable: Agent Court Work Complete")
submit_tx = contract.functions.submitDeliverable(1, deliverable_hash).build_transaction({
    "from": sender_address,
    "nonce": nonce,
    "gas": 250000,
    "gasPrice": int(w3.eth.gas_price * 1.25),
})

signed_submit = w3.eth.account.sign_transaction(submit_tx, private_key=PRIVATE_KEY)
tx_submit_hash = w3.eth.send_raw_transaction(signed_submit.raw_transaction)
print(f"Broadcasted submitDeliverable Tx: {tx_submit_hash.hex()}")
w3.eth.wait_for_transaction_receipt(tx_submit_hash)
print(" Deliverable Submitted Successfully!")

print(f"\n All 3 steps confirmed on-chain for Contract: {contract_address}")
