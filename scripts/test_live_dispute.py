import os
import sys
import json
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("BASE_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
ESCROW_ADDRESS = os.getenv("ESCROW_CONTRACT_ADDRESS", "0x541521A9a0eb01e4E395F4c43dd8Fe42d89eB723")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open(ROOT_DIR / "contracts" / "escrow_abi.json", "r") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=ESCROW_ADDRESS, abi=abi)

print(f"🏛️ Escrow Contract: {ESCROW_ADDRESS}")
print(f"👤 Caller Address: {account.address}")

current_nonce = w3.eth.get_transaction_count(account.address, "pending")

def send_tx(fn_call, gas_limit=300000):
    global current_nonce
    tx = fn_call.build_transaction({
        "from": account.address,
        "nonce": current_nonce,
        "gas": gas_limit,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    current_nonce += 1
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    time.sleep(1)
    return receipt

# 1. Create Task
spec_hash = Web3.keccak(text="Build DEX arbitrage sniper bot with WebSocket price stream and >90% coverage")
print("📦 Creating on-chain task...")
send_tx(contract.functions.createTask(account.address, 0, spec_hash))
task_id = contract.functions.taskCounter().call()
print(f"✅ Created Task #{task_id}")

# 2. Fund Task
print(f"💰 Funding Task #{task_id}...")
send_tx(contract.functions.fundTask(task_id))

# 3. Start Task
print(f"🛠️ Starting Task #{task_id}...")
send_tx(contract.functions.startTask(task_id))

# 4. Trigger Dispute
print(f"🚨 Opening dispute on Task #{task_id}...")
receipt_disp = send_tx(contract.functions.openDispute(task_id))
print(f"⚡ Dispute Opened on-chain! Block #{receipt_disp.blockNumber} (Tx: {receipt_disp.transactionHash.hex()})")
print("👉 Check your daemon_v3.py terminal to watch automated resolution.")
