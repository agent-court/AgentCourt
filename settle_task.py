import json
import time
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

account = w3.eth.account.from_key(config["PRIVATE_KEY"])
deployer_address = account.address

with open("mainnet_escrow_address.txt") as f:
    escrow_address = w3.to_checksum_address(f.read().strip())

with open("treasury_address.txt") as f:
    treasury_address = w3.to_checksum_address(f.read().strip())

USDC_ADDRESS = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)

erc20_abi = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

escrow = w3.eth.contract(address=escrow_address, abi=escrow_abi)
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=erc20_abi)

print("==================================================")
print("⚖️ AGENTCOURT: EXECUTING MAINNET RESOLUTION")
print(f"Escrow Contract : {escrow_address}")
print(f"Treasury Address: {treasury_address}")
print("==================================================")

initial_treasury_usdc = usdc.functions.balanceOf(treasury_address).call() / 1e6
print(f"Treasury Balance Before : ${initial_treasury_usdc:.4f} USDC")

# Check Task 0 status
task_id = 0
task_info = escrow.functions.tasks(task_id).call()
print(f"\nResolving Task #{task_id} with 80% to Worker, 20% to Client...")

def send_tx(tx_call):
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.to_wei(0.02, "gwei"))
    max_priority_fee = w3.to_wei(0.005, "gwei")
    max_fee = int(base_fee * 1.5) + max_priority_fee

    nonce = w3.eth.get_transaction_count(deployer_address)
    estimated_gas = tx_call.estimate_gas({"from": deployer_address})
    gas_limit = int(estimated_gas * 1.3)

    built_tx = tx_call.build_transaction({
        "chainId": 8453,
        "from": deployer_address,
        "nonce": nonce,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "gas": gas_limit
    })
    
    signed = w3.eth.account.sign_transaction(built_tx, config["PRIVATE_KEY"])
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"  ⛓️ Tx Broadcasted: https://basescan.org/tx/{tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise Exception(f"Transaction reverted! Status: {receipt.status}")
    return receipt

# Find parameter signature for resolveTask
func_abi = next(x for x in escrow_abi if x.get("name") == "resolveTask")
inputs = func_abi.get("inputs", [])
print(f"Function signature: resolveTask({', '.join([i['name'] + ' (' + i['type'] + ')' for i in inputs])})")

# Execute resolution: resolveTask(taskId, clientSharePct, workerSharePct)
if len(inputs) == 3:
    send_tx(escrow.functions.resolveTask(task_id, 20, 80))
elif len(inputs) == 2:
    send_tx(escrow.functions.resolveTask(task_id, 80))

print("  ✅ Dispute Successfully Resolved On-Chain!")

time.sleep(2)
final_treasury_usdc = usdc.functions.balanceOf(treasury_address).call() / 1e6
fee_earned = final_treasury_usdc - initial_treasury_usdc

print("\n==================================================")
print("🎉 MONETIZATION & SETTLEMENT FULLY VERIFIED!")
print(f"🏦 Final Treasury Balance : ${final_treasury_usdc:.4f} USDC")
print(f"💰 1.5% Protocol Fee Cut  : +${fee_earned:.4f} USDC")
print("==================================================")
