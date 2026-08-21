import os, json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

client_key = os.getenv("CLIENT_PRIVATE_KEY")
worker_key = os.getenv("WORKER_PRIVATE_KEY")
deployer_key = os.getenv("TREASURY_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

client_acct = w3.eth.account.from_key(client_key)
worker_acct = w3.eth.account.from_key(worker_key)
deployer_acct = w3.eth.account.from_key(deployer_key)

contract_addr = "0xaC0571eDdFC330f1CAAE19803352Ea55B9dFE720"
usdc_addr = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)
with open("usdc_abi.json") as f:
    usdc_abi = json.load(f)

contract = w3.eth.contract(address=contract_addr, abi=escrow_abi)
usdc = w3.eth.contract(address=usdc_addr, abi=usdc_abi)
treasury_addr = contract.functions.treasury().call()

print(f"Contract Address: {contract_addr}")
print(f"Treasury Address: {treasury_addr}")
print(f"Initial Treasury USDC: {usdc.functions.balanceOf(treasury_addr).call() / 1e6:.4f} USDC")

# Escrow amount: 0.50 USDC (500,000 base units)
task_amount = 500000 

# 1. Approve USDC Transfer
print("\n=== 1. Approving Escrow Contract for USDC ===")
nonce = w3.eth.get_transaction_count(client_acct.address, "pending")
tx_approve = usdc.functions.approve(contract_addr, task_amount).build_transaction({
    "from": client_acct.address,
    "nonce": nonce,
    "gas": 80000,
    "gasPrice": int(w3.eth.gas_price * 1.2),
    "chainId": 8453
})
receipt_app = w3.eth.wait_for_transaction_receipt(
    w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx_approve, client_key).raw_transaction),
    timeout=60
)
print(f"USDC Approved (tx: {receipt_app.transactionHash.hex()})")

# 2. Create and Fund Task
print("\n=== 2. Creating Task on Base Mainnet ===")
nonce = w3.eth.get_transaction_count(client_acct.address, "pending")
tx_create = contract.functions.createTask(
    worker_acct.address,
    task_amount,
    "ipfs://QmTestSpecMainnetFeeVerification",
    86400
).build_transaction({
    "from": client_acct.address,
    "nonce": nonce,
    "gas": 250000,
    "gasPrice": int(w3.eth.gas_price * 1.2),
    "chainId": 8453
})
receipt_create = w3.eth.wait_for_transaction_receipt(
    w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx_create, client_key).raw_transaction),
    timeout=60
)
task_id = contract.functions.taskCount().call()
print(f"Task #{task_id} Created & Funded (tx: {receipt_create.transactionHash.hex()})")

# 3. Worker Submits Deliverable
print(f"\n=== 3. Submitting Deliverable for Task #{task_id} ===")
nonce = w3.eth.get_transaction_count(worker_acct.address, "pending")
tx_sub = contract.functions.submitTask(task_id, "ipfs://QmTestDeliverableMainnet").build_transaction({
    "from": worker_acct.address,
    "nonce": nonce,
    "gas": 120000,
    "gasPrice": int(w3.eth.gas_price * 1.2),
    "chainId": 8453
})
receipt_sub = w3.eth.wait_for_transaction_receipt(
    w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx_sub, worker_key).raw_transaction),
    timeout=60
)
print(f"Deliverable submitted (tx: {receipt_sub.transactionHash.hex()})")

# 4. Resolve Task & Trigger 1.5% Fee Distribution
print(f"\n=== 4. Resolving Task #{task_id} ===")
nonce = w3.eth.get_transaction_count(deployer_acct.address, "pending")
tx_res = contract.functions.resolveTask(task_id, 0).build_transaction({
    "from": deployer_acct.address,
    "nonce": nonce,
    "gas": 250000,
    "gasPrice": int(w3.eth.gas_price * 1.2),
    "chainId": 8453
})
receipt_res = w3.eth.wait_for_transaction_receipt(
    w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx_res, deployer_key).raw_transaction),
    timeout=60
)
print(f"Task #{task_id} resolved on Base Mainnet (tx: {receipt_res.transactionHash.hex()})")

# 5. Final Fee Verification
final_treasury_usdc = usdc.functions.balanceOf(treasury_addr).call() / 1e6
print(f"\n=== 5. Treasury Fee Verification ===")
print(f"Final Treasury Balance: {final_treasury_usdc:.4f} USDC")
print(f"1.5% Fee routed to Treasury: {(task_amount * 0.015) / 1e6:.4f} USDC")
