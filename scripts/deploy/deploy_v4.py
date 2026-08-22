import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Deployer Address: {account.address}")
print(f"Base Sepolia Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

with open("AgentEscrowV4.json", "r") as f:
    contract_data = json.load(f)

abi = contract_data["abi"]
bytecode = contract_data["bytecode"]

EscrowContract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Deploy setting courtGateway to the deployer / agent court daemon address
construct_txn = EscrowContract.constructor(account.address).build_transaction({
    "from": account.address,
    "nonce": w3.eth.get_transaction_count(account.address),
    "gasPrice": w3.eth.gas_price,
})

signed_txn = w3.eth.account.sign_transaction(construct_txn, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
print(f"⏳ Deployment Tx Sent: https://sepolia.basescan.org/tx/{tx_hash.hex()}")

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✅ AgentEscrowV4 Deployed to: {tx_receipt.contractAddress}")

# Save the new address to .env
with open(".env", "a") as f:
    f.write(f"\nAGENT_ESCROW_V4_ADDRESS={tx_receipt.contractAddress}\n")

