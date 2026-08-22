"""
AgentCourt - 60-Second Agent-to-Agent Commercial Arbitration Hero Simulation
Demonstrates the full autonomous commerce dispute and settlement loop:
Task Creation -> Partial Delivery -> Dispute -> Precedent Lookup -> Multi-LLM Quorum -> Verdict Hash
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path

# Add repository root to Python path so modules in root are discoverable
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from web3 import Web3
from dotenv import load_dotenv

from arbitrator import deliberate_task
from vector_precedents import PrecedentEngine

load_dotenv()


def print_step(title: str):
    print(f"\n{'=' * 60}")
    print(f"🚀 {title}")
    print(f"{'=' * 60}")


def run_simulation():
    print_step("STEP 1: Agent-to-Agent Contract Formation")
    client_agent = "0xAgentClient_111111111111111111111111111111111111"
    worker_agent = "0xAgentWorker_222222222222222222222222222222222222"
    task_id = int(time.time()) % 100000

    task_spec = (
        "Task #1049: Develop an automated USDC arbitrage monitoring bot for Base Aerodrome pools.\n"
        "Requirements:\n"
        "1. Real-time WebSocket pool price listener.\n"
        "2. Slippage & gas profitability calculation module.\n"
        "3. Integration test suite with >90% coverage.\n"
        "4. Deployment runbook and Dockerfile."
    )
    spec_hash = Web3.keccak(task_spec.encode()).hex()

    print(f"💼 Client Agent: {client_agent}")
    print(f"🛠️ Worker Agent: {worker_agent}")
    print(f"💰 Escrow Amount: 100.00 USDC")
    print(f"📜 Spec Hash: {spec_hash}")
    time.sleep(1)

    print_step("STEP 2: Deliverable Submission & Dispute Trigger")
    deliverable = (
        "Deliverable Submission:\n"
        "Completed items:\n"
        "- WebSocket pool price listener implemented and operational.\n"
        "- Slippage calculation logic completed.\n"
        "Incomplete/Deferred:\n"
        "- Gas estimation logic omitted due to RPC rate limiting.\n"
        "- Test coverage reached 65% (below 90% target).\n"
        "- Dockerfile provided."
    )
    deliverable_hash = Web3.keccak(deliverable.encode()).hex()

    print(f"📦 Deliverable Hash: {deliverable_hash}")
    print("⚠️ Client Agent Audit: Requirements #2 and #3 partially unfulfilled.")
    print(f"🚨 On-Chain Dispute Opened on Task #{task_id}")
    time.sleep(1)

    print_step("STEP 3: Vector Precedent Retrieval (Machine Stare Decisis)")
    engine = PrecedentEngine()

    # Seed baseline precedent if empty
    if engine.collection.count() == 0:
        engine.record_precedent(
            case_id="case_baseline_partial_delivery",
            facts="Worker completed 75% of bot features but missed automated test coverage requirement.",
            issue="Partial contractual fulfillment on software delivery.",
            worker_bps=7000,
            client_bps=3000,
            reasoning="Substantial core infrastructure provided; penalty assessed for missing test suite."
        )

    precedents = engine.query_precedents(
        query_text=f"Arbitrage bot partial delivery test coverage missing: {deliverable}",
        top_k=2
    )

    print(f"🏛️ Case Law Matches Retrieved: {len(precedents)}")
    for p in precedents:
        print(f"   • {p['case_id']}: Historical Worker Payout = {p['worker_bps']} BPS ({p['worker_bps']/100:.1f}%)")
    time.sleep(1)

    print_step("STEP 4: Multi-Model AI Panel Deliberation (Zero-Temperature)")
    print("⏳ Deliberating across independent juror models with prompt-injection shielding...")

    try:
        result = deliberate_task(
            task_id=task_id,
            task_spec=task_spec,
            deliverable=deliverable,
            precedents=precedents,
            min_quorum=1
        )
    except Exception as e:
        print(f"⚠️ Deliberation error: {e}")
        return

    print("\n📊 Juror Votes & Evidence Breakdown:")
    for v in result.juror_votes:
        print(f"\n⚖️ Juror: {v.juror_id} ({v.model_name})")
        print(f"   Breach Detected: {v.breach_detected}")
        print(f"   Allocation: Worker {v.worker_bps} BPS ({v.worker_bps/100:.1f}%) | Client {v.client_bps} BPS ({v.client_bps/100:.1f}%)")
        print(f"   Confidence: {v.confidence:.2f}")
        print(f"   Reasoning: {v.reasoning}")

    print_step("STEP 5: Deterministic Quorum & Cryptographic Settlement")
    print(f"🏛️ Final Consensus Allocation: Worker {result.consensus_worker_bps} BPS | Client {result.consensus_client_bps} BPS")
    print(f"🔒 Canonical Verdict Hash (bytes32): {result.verdict_hash}")

    # Calculate financial disbursement
    total_usdc = 100.00
    protocol_fee = total_usdc * 0.015
    net_funds = total_usdc - protocol_fee
    worker_payout = net_funds * (result.consensus_worker_bps / 10000.0)
    client_refund = net_funds - worker_payout

    print("\n💵 On-Chain Financial Settlement Summary:")
    print(f"   • Escrowed Total: ${total_usdc:.2f} USDC")
    print(f"   • Protocol Fee (1.5%): ${protocol_fee:.2f} USDC -> Treasury")
    print(f"   • Worker Disbursement: ${worker_payout:.2f} USDC -> {worker_agent}")
    print(f"   • Client Refund: ${client_refund:.2f} USDC -> {client_agent}")

    engine.record_precedent(
        case_id=f"case_{task_id}",
        facts=task_spec,
        issue="Partial delivery of arbitrage bot requirements",
        worker_bps=result.consensus_worker_bps,
        client_bps=result.consensus_client_bps,
        reasoning=result.juror_votes[0].reasoning if result.juror_votes else "Consensus ruling",
        verdict_hash=result.verdict_hash
    )

    print(f"\n✅ Case #{task_id} sealed and indexed into AgentCourt Case Law.")


if __name__ == "__main__":
    run_simulation()
