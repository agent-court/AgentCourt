import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv
from daemon_v4 import process_evaluation

load_dotenv()

RPC_URL = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ESCROW_ADDRESS = "0x0233B2B49788204ddd00Fb39508b944aC3904F71"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open("AgentEscrowV4.json", "r") as f:
    contract_data = json.load(f)

contract = w3.eth.contract(address=ESCROW_ADDRESS, abi=contract_data["abi"])

print("==================================================")
print("🚀 RUNNING ERC-8183 AGENTCOURT END-TO-END SIMULATION")
print("==================================================")

# 1. CREATE JOB (State 0: Open)
provider_addr = account.address
evaluator_addr = account.address
expiry = int(time.time()) + 86400
task_hash = w3.keccak(text="Build a Python FastAPI endpoint with JWT auth and rate limiting.")

print("\n1️⃣ Creating ERC-8183 Job...")
nonce = w3.eth.get_transaction_count(account.address, 'pending')
gas_price = int(w3.eth.gas_price * 1.25)

tx = contract.functions.createJob(
    provider_addr,
    evaluator_addr,
    expiry,
    task_hash
).build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gasPrice": gas_price
})
signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash)
job_id = contract.functions.jobCount().call()
print(f"✅ Job #{job_id} Created on-chain (Tx: {tx_hash.hex()})")
time.sleep(3)

# 2. FUND JOB (State 1: Funded)
print(f"\n2️⃣ Funding Job #{job_id} with 0.0001 ETH...")
nonce = w3.eth.get_transaction_count(account.address, 'pending')
gas_price = int(w3.eth.gas_price * 1.25)

fund_tx = contract.functions.fundJob(job_id).build_transaction({
    "from": account.address,
    "value": w3.to_wei(0.0001, "ether"),
    "nonce": nonce,
    "gasPrice": gas_price
})
signed_fund = w3.eth.account.sign_transaction(fund_tx, private_key=PRIVATE_KEY)
tx_fund_hash = w3.eth.send_raw_transaction(signed_fund.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_fund_hash)
print(f"✅ Job #{job_id} Funded! (Tx: {tx_fund_hash.hex()})")
time.sleep(3)

# 3. SUBMIT DELIVERABLE (State 2: Submitted)
print(f"\n3️⃣ Provider Submitting Deliverable Proof...")
deliverable_hash = w3.keccak(text="Implemented JWT auth endpoints, omitted rate limiting.")
nonce = w3.eth.get_transaction_count(account.address, 'pending')
gas_price = int(w3.eth.gas_price * 1.25)

submit_tx = contract.functions.submitDeliverable(job_id, deliverable_hash).build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gasPrice": gas_price
})
signed_submit = w3.eth.account.sign_transaction(submit_tx, private_key=PRIVATE_KEY)
tx_submit_hash = w3.eth.send_raw_transaction(signed_submit.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_submit_hash)
print(f"✅ Deliverable Hash Anchored! (Tx: {tx_submit_hash.hex()})")
time.sleep(3)

# 4. RUN AI COURT DELIBERATION & ON-CHAIN EVALUATION (State 3: Terminal)
print(f"\n4️⃣ Triggering ChromaDB-Powered Synthetic Jury & Settlement...")
spec = "Build a Python FastAPI endpoint with JWT auth and rate limiting."
evidence = "Worker delivered functional JWT authentication endpoints, but completely omitted the Redis rate limiter module."

process_evaluation(job_id=job_id, task_spec=spec, deliverable_evidence=evidence)

# 5. VERIFY FINAL ON-CHAIN STATUS
job_info = contract.functions.jobs(job_id).call()
status_names = ["Open", "Funded", "Submitted", "Terminal"]
print(f"\n🏁 Final Job #{job_id} On-Chain Status: {status_names[job_info[8]]} | Worker Basis Points: {job_info[9]} BPS")
print("==================================================")
