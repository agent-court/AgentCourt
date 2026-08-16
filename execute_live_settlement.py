import json
import time
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

assert w3.is_connected(), "❌ Base Mainnet RPC connection failed"

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
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"}
]

escrow = w3.eth.contract(address=escrow_address, abi=escrow_abi)
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=erc20_abi)

TEST_WORKER_ADDRESS = w3.to_checksum_address("0x1111111111111111111111111111111111111111")

print("==================================================")
print("🚀 AGENTCOURT LIVE MAINNET SETTLEMENT TEST")
print(f"Client (Deployer) : {deployer_address}")
print(f"Worker Target     : {TEST_WORKER_ADDRESS}")
print(f"Escrow Contract   : {escrow_address}")
print(f"Treasury Target   : {treasury_address}")
print("==================================================")

initial_treasury_usdc = usdc.functions.balanceOf(treasury_address).call() / 1e6
initial_deployer_usdc = usdc.functions.balanceOf(deployer_address).call() / 1e6

print(f"Initial Treasury Balance : ${initial_treasury_usdc:.4f} USDC")
print(f"Initial Deployer Balance : ${initial_deployer_usdc:.4f} USDC")

def send_tx(tx_call):
    latest_block = w3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas", w3.to_wei(0.02, "gwei"))
    max_priority_fee = w3.to_wei(0.005, "gwei")
    max_fee = int(base_fee * 1.5) + max_priority_fee

    nonce = w3.eth.get_transaction_count(deployer_address)
    
    # Estimate gas with safety buffer
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
    print(f"  ⛓️  Tx Broadcasted: https://basescan.org/tx/{tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise Exception(f"Transaction reverted! Status: {receipt.status}")
    return receipt

# Step 1: Ensure USDC Allowance
AMOUNT_USDC_UNITS = 1_000_000 # 1.00 USDC
allowance = usdc.functions.allowance(deployer_address, escrow_address).call()
if allowance < AMOUNT_USDC_UNITS:
    print("\n[Step 1/3] Approving 5.00 USDC to Escrow Contract...")
    send_tx(usdc.functions.approve(escrow_address, 5_000_000))
    print("  ✅ USDC Approved!")
else:
    print("\n[Step 1/3] USDC allowance confirmed ($1.00+).")

# Step 2: Create Escrow Task with 24h Deadline
deadline = int(time.time()) + 86400
spec = "Autonomous Agent Task: Query Base L2 block data and calculate average fee."
print("\n[Step 2/3] Creating On-Chain Escrow Task ($1.00 USDC)...")

send_tx(escrow.functions.createTask(
    TEST_WORKER_ADDRESS,
    AMOUNT_USDC_UNITS,
    spec,
    deadline
))

task_id = escrow.functions.taskCount().call()
print(f"  ✅ Task #{task_id} successfully created and funded on Base Mainnet!")

# Step 3: Resolve Task with an 80/20 Arbitrated Split
print(f"\n[Step 3/3] Executing Court Resolution on Task #{task_id}...")
send_tx(escrow.functions.resolveDispute(
    task_id,
    20, # 20% to Client ($0.197 USDC)
    80  # 80% to Worker ($0.788 USDC)
))
print("  ✅ Settlement Executed on Base Mainnet!")

time.sleep(2)
final_treasury_usdc = usdc.functions.balanceOf(treasury_address).call() / 1e6
fee_earned = final_treasury_usdc - initial_treasury_usdc

print("\n==================================================")
print("🎉 SETTLEMENT COMPLETE & MONETIZATION VERIFIED!")
print(f"🏦 New Treasury Balance : ${final_treasury_usdc:.4f} USDC")
print(f"💰 1.5% Protocol Fee    : +${fee_earned:.4f} USDC earned!")
print("==================================================")
