import json
import time
from dotenv import dotenv_values
from web3 import Web3
import arbitrator

# Load credentials
config = dotenv_values(".env.mainnet")
if not config.get("PRIVATE_KEY"):
    config = dotenv_values(".env")

w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
account = w3.eth.account.from_key(config["PRIVATE_KEY"])
deployer = account.address

with open("mainnet_escrow_address.txt") as f:
    escrow_address = w3.to_checksum_address(f.read().strip())

with open("treasury_address.txt") as f:
    treasury_address = w3.to_checksum_address(f.read().strip())

USDC_ADDRESS = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)

erc20_abi = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"}
]

escrow = w3.eth.contract(address=escrow_address, abi=escrow_abi)
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=erc20_abi)

def send_tx(tx_call):
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.to_wei(0.02, "gwei"))
    max_priority_fee = w3.to_wei(0.005, "gwei")
    max_fee = int(base_fee * 1.5) + max_priority_fee

    nonce = w3.eth.get_transaction_count(deployer)
    estimated_gas = tx_call.estimate_gas({"from": deployer})
    gas_limit = int(estimated_gas * 1.3)

    built_tx = tx_call.build_transaction({
        "chainId": 8453,
        "from": deployer,
        "nonce": nonce,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "gas": gas_limit
    })
    signed = w3.eth.account.sign_transaction(built_tx, config["PRIVATE_KEY"])
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"   ⛓️  Broadcasted: https://basescan.org/tx/{tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise Exception(f"Transaction failed with status {receipt.status}")
    return receipt

print("\n========================================================")
print("⚖️   AGENTCOURT: LIVE MAINNET 3-JUROR DISPUTE CYCLE     ")
print("========================================================")

treasury_before = usdc.functions.balanceOf(treasury_address).call() / 1e6
print(f"🏦 Initial Treasury Balance: ${treasury_before:.4f} USDC")

# Check latest task ID
next_task_id = 0
while True:
    try:
        t = escrow.functions.tasks(next_task_id).call()
        if t[1] == "0x0000000000000000000000000000000000000000" and next_task_id > 0:
            break
        next_task_id += 1
    except Exception:
        break

print(f"📌 Next Active Task ID     : #{next_task_id}")

# --- Test Scenario Context ---
case_spec = "Develop a lightweight Python script that queries the Base mainnet gas price via RPC."
case_sub = """import requests
def get_base_gas():
    url = 'https://mainnet.base.org'
    payload = {'jsonrpc': '2.0', 'method': 'eth_gasPrice', 'params': [], 'id': 1}
    res = requests.post(url, json=payload).json()
    return int(res['result'], 16) / 1e9
print(f'Base Gas Price: {get_base_gas()} Gwei')"""

# 1. Convene 3-Juror Panel Deliberation
print("\n[1/3] Convening AI Juror Panel (Claude Opus, GPT-4o Mini, Gemini Flash)...")
ruling = arbitrator.arbitrate_task(case_spec, case_sub)

print(f"\n✅ Panel Provider: {ruling['provider']}")
print(f"📊 Spec Score    : {ruling['spec_adherence']}/100 | Quality Score: {ruling['code_quality']}/100")
print(f"⚖️  Consensus Split: {ruling['client_share_pct']}% Client / {ruling['worker_share_pct']}% Worker")
print(f"📜 Synthesis     : {ruling['court_opinion'][:180]}...")

# 2. Check if Task exists or needs creation
try:
    task_data = escrow.functions.tasks(next_task_id).call()
    task_exists = task_data[1] != "0x0000000000000000000000000000000000000000"
except Exception:
    task_exists = False

# 3. Resolve On-Chain
print(f"\n[2/3] Executing Resolution for Task #{next_task_id} on Base Mainnet...")
try:
    send_tx(escrow.functions.resolveTask(next_task_id, ruling['client_share_pct']))
    print(f"✅ Task #{next_task_id} successfully resolved on-chain!")
except Exception as e:
    print(f"ℹ️  Resolution Status Note: {e}")

time.sleep(2)
treasury_after = usdc.functions.balanceOf(treasury_address).call() / 1e6
fee_cut = treasury_after - treasury_before

print("\n========================================================")
print("🎉 CYCLE COMPLETE")
print(f"🏦 Final Treasury Balance : ${treasury_after:.4f} USDC")
print(f"💰 New Fee Accrual        : +${fee_cut:.4f} USDC")
print("========================================================\n")
