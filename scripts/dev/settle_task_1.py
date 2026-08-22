import time
from dotenv import dotenv_values
from web3 import Web3
import json

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

account = w3.eth.account.from_key(config["PRIVATE_KEY"])
deployer = account.address

with open("mainnet_escrow_address.txt") as f:
    escrow_addr = w3.to_checksum_address(f.read().strip())

with open("treasury_address.txt") as f:
    treasury_addr = w3.to_checksum_address(f.read().strip())

USDC_ADDR = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)

erc20_abi = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

escrow = w3.eth.contract(address=escrow_addr, abi=escrow_abi)
usdc = w3.eth.contract(address=USDC_ADDR, abi=erc20_abi)

print("==================================================")
print("⚖️ EXECUTING MAINNET RESOLUTION ON TASK #1")
print(f"Contract: {escrow_addr}")
print(f"Treasury: {treasury_addr}")
print("==================================================")

treasury_before = usdc.functions.balanceOf(treasury_addr).call() / 1e6
print(f"Treasury USDC Before: ${treasury_before:.4f} USDC")

latest_block = w3.eth.get_block("latest")
base_fee = latest_block.get("baseFeePerGas", w3.to_wei(0.02, "gwei"))
max_priority_fee = w3.to_wei(0.005, "gwei")
max_fee = int(base_fee * 1.5) + max_priority_fee

nonce = w3.eth.get_transaction_count(deployer)

# Resolve Task #1 with 20% to Client
tx_call = escrow.functions.resolveTask(1, 20)
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
print(f"⛓️  Tx Broadcasted: https://basescan.org/tx/{tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
assert receipt.status == 1, "Transaction reverted!"

time.sleep(2)
treasury_after = usdc.functions.balanceOf(treasury_addr).call() / 1e6
fee_earned = treasury_after - treasury_before

print("\n==================================================")
print("🎉 TASK #1 RESOLVED & PROTOCOL FEE EARNED!")
print(f"🏦 New Treasury Balance : ${treasury_after:.4f} USDC")
print(f"💰 1.5% Fee Accrued     : +${fee_earned:.4f} USDC")
print("==================================================")
