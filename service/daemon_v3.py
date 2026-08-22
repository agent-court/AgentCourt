"""
AgentCourt - Background Dispute Listener & Automated Juror Daemon
Listens for DisputeOpened events, runs deterministic deliberation, and posts rulings on Base.
"""

import os
import time
import json
from web3 import Web3
from dotenv import load_dotenv

from arbitrator import deliberate_task, ArbitrationQuorumError
from vector_precedents import PrecedentEngine

load_dotenv()

RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
ESCROW_ADDRESS = os.getenv("AGENT_ESCROW_ADDRESS")
OPERATOR_KEY = os.getenv("OPERATOR_PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
engine = PrecedentEngine()

with open("contracts/escrow_abi.json", "r") as f:
    ESCROW_ABI = json.load(f)

def run_daemon(poll_interval: int = 12):
    if not ESCROW_ADDRESS or not OPERATOR_KEY:
        print("❌ AGENT_ESCROW_ADDRESS or OPERATOR_PRIVATE_KEY missing in environment.")
        return

    account = w3.eth.account.from_key(OPERATOR_KEY)
    contract = w3.eth.contract(address=w3.to_checksum_address(ESCROW_ADDRESS), abi=ESCROW_ABI)
    print(f"⚖️ AgentCourt Daemon active on Base. Court Operator: {account.address}")

    # Listen for live DisputeOpened events
    event_filter = contract.events.DisputeOpened.create_filter(from_block="latest")

    while True:
        try:
            for event in event_filter.get_new_entries():
                task_id = event.args.taskId
                initiator = event.args.initiator
                print(f"\n🚨 New Dispute Detected on Task #{task_id} (Opened by {initiator})")

                # Fetch task data on-chain
                task = contract.functions.tasks(task_id).call()
                spec_hash = task[5].hex()
                deliverable_hash = task[6].hex()

                # Semantic query against case law
                search_query = f"Task #{task_id} SpecHash: {spec_hash} Deliverables: {deliverable_hash}"
                precedents = engine.query_precedents(search_query, top_k=3)

                # Run multi-model consensus
                try:
                    result = deliberate_task(
                        task_id=task_id,
                        task_spec=f"Spec Hash: {spec_hash}",
                        deliverable=f"Deliverables Hash: {deliverable_hash}",
                        precedents=precedents
                    )
                except ArbitrationQuorumError as err:
                    print(f"⚠️ Deliberation halted: {err}")
                    continue

                print(f"🏛️ Consensus Reached: Worker {result.consensus_worker_bps} BPS | Client {result.consensus_client_bps} BPS")
                print(f"🔒 Verdict Hash: {result.verdict_hash}")

                # Build on-chain resolve transaction
                tx = contract.functions.resolveDispute(
                    task_id,
                    result.consensus_worker_bps,
                    bytes.fromhex(result.verdict_hash[2:] if result.verdict_hash.startswith("0x") else result.verdict_hash)
                ).build_transaction({
                    "from": account.address,
                    "nonce": w3.eth.get_transaction_count(account.address),
                    "gasPrice": w3.eth.gas_price
                })

                signed_tx = w3.eth.account.sign_transaction(tx, OPERATOR_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                print(f"✅ Dispute Resolved On-Chain. Tx: {tx_hash.hex()}")

                # Record new precedent into case law engine
                engine.record_precedent(
                    case_id=f"case_{task_id}",
                    facts=f"Task #{task_id} dispute between {task[0]} and {task[1]}",
                    issue="Contractual deliverables satisfaction",
                    worker_bps=result.consensus_worker_bps,
                    client_bps=result.consensus_client_bps,
                    reasoning=result.juror_votes[0].reasoning if result.juror_votes else "Consensus ruling",
                    verdict_hash=result.verdict_hash
                )

            time.sleep(poll_interval)
        except Exception as e:
            print(f"⚠️ Polling loop error: {e}")
            time.sleep(poll_interval)


if __name__ == "__main__":
    run_daemon()
