import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from agentcourt import AgentCourtClient
from vector_precedents import PrecedentEngine

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
if not PRIVATE_KEY:
    print("❌ Error: PRIVATE_KEY not found")
    sys.exit(1)

client = AgentCourtClient(private_key=PRIVATE_KEY)
engine = PrecedentEngine()

test_cases = [
    {
        "title": "Benchmark Case A: Full Specification Match",
        "spec": "Develop an automated ERC-20 staking contract with emergency withdrawal functions.",
        "deliverable": "Staking contract with standard deposits, rewards distribution, and fully tested emergency withdrawal."
    },
    {
        "title": "Benchmark Case B: Partial Spec Delivery",
        "spec": "Create high-throughput WebSocket price ticker indexing Uniswap V3 pools with unit tests.",
        "deliverable": "WebSocket price ticker operational, but unit tests were omitted entirely."
    },
    {
        "title": "Benchmark Case C: Broken Contract Scope",
        "spec": "Implement gas-optimized Merkle tree airdrop distributor in Solidity with fuzz testing.",
        "deliverable": "Submitted incomplete Python mockup without smart contracts."
    }
]

print("=" * 65)
print("⚡ AgentCourt V5 — Multi-Case Consensus Benchmark")
print("=" * 65)

results = []

for idx, case in enumerate(test_cases, 1):
    print(f"\n[{idx}/3] Executing {case['title']}...")
    t0 = time.time()
    
    # 1. On-Chain Lifecycle Creation
    task_id = client.create_task(client.account.address, 0, case["spec"])
    client.fund_task(task_id)
    client.start_task(task_id)
    client.open_dispute(task_id)
    
    t_lifecycle = time.time() - t0
    print(f"  • Task #{task_id} Disputed on Base Sepolia ({t_lifecycle:.2f}s)")
    
    # 2. Benchmark Precedent Query
    t_vec_start = time.time()
    citations = engine.retrieve_precedents(f"{case['spec']} {case['deliverable']}", top_k=2) if hasattr(engine, "retrieve_precedents") else []
    t_vec = time.time() - t_vec_start
    print(f"  • Retrieved {len(citations)} ChromaDB Precedents ({t_vec*1000:.1f}ms)")
    
    results.append({
        "task_id": task_id,
        "name": case["title"],
        "lifecycle_sec": round(t_lifecycle, 2),
        "vector_query_ms": round(t_vec * 1000, 1)
    })

print("\n" + "=" * 65)
print("📊 Benchmark Results Summary:")
print("=" * 65)
for r in results:
    print(f"• Task #{r['task_id']} | Lifecycle: {r['lifecycle_sec']}s | Vector Query: {r['vector_query_ms']}ms | {r['name']}")
print("=" * 65)
