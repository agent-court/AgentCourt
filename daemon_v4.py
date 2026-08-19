import os
import time
import json
from web3 import Web3
from dotenv import load_dotenv
from vector_precedents import find_relevant_precedents
from arbitrator import arbitrate_task

load_dotenv()

RPC_URL = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ESCROW_ADDRESS = os.getenv("AGENT_ESCROW_V4_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
court_account = w3.eth.account.from_key(PRIVATE_KEY)

with open("AgentEscrowV4.json", "r") as f:
    contract_data = json.load(f)

contract = w3.eth.contract(address=ESCROW_ADDRESS, abi=contract_data["abi"])

print(f"🏛️ AgentCourt Daemon V4 Active")
print(f"   Listening on Base Sepolia: {ESCROW_ADDRESS}")
print(f"   Court Executor: {court_account.address}")


def process_evaluation(job_id: int, task_spec: str, deliverable_evidence: str):
    print(f"\n⚖️ Initiating Deliberation for Job #{job_id}...")
    
    # 1. Retrieve ChromaDB vector precedents
    precedents = find_relevant_precedents(task_spec, deliverable_evidence, top_k=2)
    print(f"📚 Precedents retrieved from ChromaDB: {len(precedents)} cases.")

    # 2. Run multi-agent jury panel
    ruling = arbitrate_task(task_spec, deliverable_evidence)
    
    worker_split_bps = int(ruling.get("worker_share_pct", 50) * 100)
    opinion = ruling.get("court_opinion", "Consensus reached by synthetic jury.")
    
    print(f"📊 Jury Verdict: {worker_split_bps / 100}% Payout to Worker ({worker_split_bps} BPS)")

    # 3. Settle on-chain via evaluateJob
    tx = contract.functions.evaluateJob(
        job_id,
        worker_split_bps,
        opinion[:500]  # Truncate opinion for gas optimization
    ).build_transaction({
        "from": court_account.address,
        "nonce": w3.eth.get_transaction_count(court_account.address),
        "gasPrice": w3.eth.gas_price
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"🚀 Settlement Tx: https://sepolia.basescan.org/tx/{tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Job #{job_id} successfully settled on Base Sepolia in block {receipt.blockNumber}!")


if __name__ == "__main__":
    print("✨ Daemon ready for evaluation loop triggers.")
