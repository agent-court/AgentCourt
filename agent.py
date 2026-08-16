import json
import os
import time
from dotenv import load_dotenv
from web3 import Web3
import arbitrator

load_dotenv(override=True)

PRIVATE_KEY = os.getenv("PRIVATE_KEY", "").strip()
RPC_URL = os.getenv("RPC_URL", "https://base-sepolia-rpc.publicnode.com").strip()

assert PRIVATE_KEY, "❌ PRIVATE_KEY missing in .env file"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), "❌ Could not connect to Base Sepolia"

def get_raw_tx(signed_tx):
    return getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))

with open("contract_address.txt") as f:
    ESCROW_ADDRESS = w3.to_checksum_address(f.read().strip())

with open("usdc_address.txt") as f:
    USDC_ADDRESS = w3.to_checksum_address(f.read().strip())

with open("contract_abi.json") as f:
    ESCROW_ABI = json.load(f)

with open("usdc_abi.json") as f:
    USDC_ABI = json.load(f)

escrow_contract = w3.eth.contract(address=ESCROW_ADDRESS, abi=ESCROW_ABI)
usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)

client_account = w3.eth.account.from_key(PRIVATE_KEY)
CLIENT_ADDR = client_account.address
CHAIN_ID = 84532

if os.path.exists("worker_key.txt"):
    with open("worker_key.txt") as f:
        WORKER_KEY = f.read().strip()
else:
    WORKER_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

worker_account = w3.eth.account.from_key(WORKER_KEY)
WORKER_ADDR = worker_account.address

def to_usdc(amount_dollars: float) -> int:
    return int(amount_dollars * 10**6)

def build_tx_with_gas(func_call, from_addr, fallback_gas=450000):
    nonce = w3.eth.get_transaction_count(from_addr, "pending")
    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    max_priority_fee = w3.to_wei("0.1", "gwei")
    max_fee = int(base_fee * 2) + max_priority_fee

    try:
        est_gas = func_call.estimate_gas({"from": from_addr})
        gas_limit = int(est_gas * 1.3)
    except Exception:
        gas_limit = fallback_gas

    return func_call.build_transaction({
        "from": from_addr,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": gas_limit,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "type": 2,
    })

def send_and_wait(tx_dict, private_key):
    signed = w3.eth.account.sign_transaction(tx_dict, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError(f"❌ Transaction failed/reverted on-chain: {tx_hash.hex()}")
    return tx_hash, receipt

def create_task_usdc(
    worker_addr: str, details_hash: str, amount_usd: float = 1.00, duration_seconds: int = 3600
) -> int:
    raw_amount = to_usdc(amount_usd)

    # 1. Allowance Check
    allowance = usdc_contract.functions.allowance(CLIENT_ADDR, ESCROW_ADDRESS).call()
    if allowance < raw_amount:
        func = usdc_contract.functions.approve(ESCROW_ADDRESS, 1000 * 10**6)
        tx = build_tx_with_gas(func, CLIENT_ADDR, fallback_gas=100000)
        tx_hash, _ = send_and_wait(tx, PRIVATE_KEY)
        print(f"1. 🔓 Approved USDC for Escrow Contract on Base Sepolia")
        time.sleep(1)
    else:
        print(f"1. 🔓 Existing USDC allowance sufficient")

    # 2. Create Task
    func = escrow_contract.functions.createTask(
        w3.to_checksum_address(worker_addr),
        raw_amount,
        details_hash,
        duration_seconds,
    )
    tx = build_tx_with_gas(func, CLIENT_ADDR, fallback_gas=450000)
    tx_hash, receipt = send_and_wait(tx, PRIVATE_KEY)
    
    logs = escrow_contract.events.TaskCreated().process_receipt(receipt)
    if logs:
        task_id = logs[0]["args"]["taskId"]
    else:
        task_id = escrow_contract.functions.taskCount().call()

    print(f"2. 🟢 Task #{task_id} Created on Base Sepolia! Tx: {tx_hash.hex()}")
    return task_id

def submit_task(task_id: int, deliverable_text: str):
    time.sleep(1)
    func = escrow_contract.functions.submitTask(task_id, deliverable_text)
    tx = build_tx_with_gas(func, WORKER_ADDR, fallback_gas=200000)
    tx_hash, _ = send_and_wait(tx, WORKER_KEY)
    print(f"3. 🟡 Deliverables Submitted by Worker for Task #{task_id} on Base Sepolia")

def ai_evaluate_and_resolve(task_id: int, task_terms: str, submission: str):
    print("\n🤖 AI Court Arbitrator reviewing deliverables...")

    ruling = arbitrator.arbitrate_task(task_terms, submission)
    client_share = ruling["client_share_pct"]
    worker_share = ruling["worker_share_pct"]

    print(f"🏛️ AI COURT OPINION ({ruling['provider']}):")
    print(f"   Spec Adherence : {ruling['spec_adherence']}%")
    print(f"   Code Quality   : {ruling['code_quality']}%")
    print(f"   Ruling         : {client_share}% to Client | {worker_share}% to Worker")
    print(f"   Opinion        : {ruling['court_opinion']}\n")

    time.sleep(1)
    func = escrow_contract.functions.resolveTask(task_id, client_share)
    tx = build_tx_with_gas(func, CLIENT_ADDR, fallback_gas=350000)
    tx_hash, _ = send_and_wait(tx, PRIVATE_KEY)
    print(f"4. ✅ On-Chain Settlement Finalized on Base Sepolia! Tx: {tx_hash.hex()}")

if __name__ == "__main__":
    print(f"🔗 Connected to Base Sepolia Testnet | Account: {CLIENT_ADDR}\n")
    task_spec = "Write a Python function `calc_discount(price, pct)` that returns the final price."
    worker_code = "def calc_discount(price, pct):\n    return price * (1 - pct/100)"

    task_id = create_task_usdc(WORKER_ADDR, task_spec, 1.00, duration_seconds=3600)
    submit_task(task_id, worker_code)
    ai_evaluate_and_resolve(task_id, task_spec, worker_code)

    print(f"\n🎉 Basescan Explorer: https://sepolia.basescan.org/address/{ESCROW_ADDRESS}")
