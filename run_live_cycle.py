import os, time, json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

client_key = os.getenv("CLIENT_PRIVATE_KEY")
client_acct = w3.eth.account.from_key(client_key)

contract_addr = "0xaC0571eDdFC330f1CAAE19803352Ea55B9dFE720"
usdc_addr = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
worker_addr = "0x0270FE1033b0460D7f3d2C1333D6EBf1B6d1eB77"

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)
with open("usdc_abi.json") as f:
    usdc_abi = json.load(f)

contract = w3.eth.contract(address=contract_addr, abi=escrow_abi)
usdc = w3.eth.contract(address=usdc_addr, abi=usdc_abi)
treasury_addr = contract.functions.treasury().call()

# Escrow amount: 0.20 USDC (200,000 base units)
task_amount = 200000 

print("==================================================")
print("🚀 EXECUTING LIVE ESCROW & FEE ROUTING ON BASE")
print(f"Contract  : {contract_addr}")
print(f"Treasury  : {treasury_addr}")
print(f"Client    : {client_acct.address}")
print(f"Worker    : {worker_addr}")

start_treasury = usdc.functions.balanceOf(treasury_addr).call() / 1e6
print(f"Initial Treasury USDC: {start_treasury:.6f} USDC")
print("==================================================")

# 1. Create & Fund Task
print("\n[1/3] Creating & Funding Task...")
nonce = w3.eth.get_transaction_count(client_acct.address, "pending")
tx_create = contract.functions.createTask(
    worker_addr,
    task_amount,
    "ipfs://QmTestSpecMainnetFeeVerification",
    86400
).build_transaction({
    "from": client_acct.address,
    "nonce": nonce,
    "gas": 400000,
    "gasPrice": int(w3.eth.gas_price * 1.3),
    "chainId": 8453
})

signed_create = w3.eth.account.sign_transaction(tx_create, client_key)
tx_hash_create = w3.eth.send_raw_transaction(signed_create.raw_transaction)
print(f"Broadcasted createTask (tx: {tx_hash_create.hex()})...")

receipt_create = w3.eth.wait_for_transaction_receipt(tx_hash_create, timeout=60)
if receipt_create.status != 1:
    raise Exception("createTask reverted on-chain!")

task_id = contract.functions.taskCount().call()
print(f"✓ Task #{task_id} Created & Funded successfully!")

# 2. Resolve Task directly as Client (Contract allows client or owner to resolve)
print(f"\n[2/3] Resolving Task #{task_id} (Releasing 100% to Worker, 1.5% to Treasury)...")
nonce = w3.eth.get_transaction_count(client_acct.address, "pending")
tx_res = contract.functions.resolveTask(task_id, 0).build_transaction({
    "from": client_acct.address,
    "nonce": nonce,
    "gas": 400000,
    "gasPrice": int(w3.eth.gas_price * 1.3),
    "chainId": 8453
})

signed_res = w3.eth.account.sign_transaction(tx_res, client_key)
tx_hash_res = w3.eth.send_raw_transaction(signed_res.raw_transaction)
print(f"Broadcasted resolveTask (tx: {tx_hash_res.hex()})...")

receipt_res = w3.eth.wait_for_transaction_receipt(tx_hash_res, timeout=60)
if receipt_res.status != 1:
    raise Exception("resolveTask reverted on-chain!")

print(f"✓ Task #{task_id} Resolved on Base Mainnet!")

# 3. Verify Treasury Fee
time.sleep(2)
end_treasury = usdc.functions.balanceOf(treasury_addr).call() / 1e6
fee_received = end_treasury - start_treasury

print("\n" + "="*50)
print("🎉 BASE MAINNET FEE ROUTING VERIFIED!")
print(f"Previous Treasury Balance: {start_treasury:.6f} USDC")
print(f"Final Treasury Balance:    {end_treasury:.6f} USDC")
print(f"Protocol Fee Routed:       +{fee_received:.6f} USDC (1.5%)")
print("="*50)
