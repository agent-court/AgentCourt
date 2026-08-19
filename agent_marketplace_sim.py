import os
import time
from dotenv import load_dotenv

load_dotenv()

from sdk.agentcourt.client import AgentCourtClient

DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
if not DEPLOYER_KEY:
    raise ValueError("Please set DEPLOYER_PRIVATE_KEY in your .env file.")

# Initialize SDK Client
client = AgentCourtClient(private_key=DEPLOYER_KEY)
contractor_agent_address = "0xAe679030eD87b126B726A3e7d73e58e633465d76"

print("=" * 60)
print("🤖 AGENTCOURT: AUTONOMOUS AGENT-TO-AGENT WORKFLOW")
print("=" * 60)

# 1. Employer Agent creates task
task_brief = "Analyze top 5 liquidity pools on Base and return JSON summary"
print(f"\n[Agent A - Employer] Publishing task: '{task_brief}'")
print("[Agent A - Employer] Depositing 0.0001 ETH into on-chain escrow...")

create_tx, task_id = client.create_task(
    contractor=contractor_agent_address,
    spec_uri="ipfs://base-dex-analytics-v1",
    amount_eth=0.0001,
    challenge_period=300
)
print(f"💰 Escrow Locked! Task #{task_id} on Base Sepolia | TX: {create_tx}")

# 2. Worker Agent delivers mock output
print(f"\n[Agent B - Worker] Processing specification 'ipfs://base-dex-analytics-v1'...")
time.sleep(2)
mock_deliverable = {
    "status": "partial_failure",
    "pools_analyzed": 2, # Failed requirement (requested 5)
    "data": ["Aerodrome USDC/ETH", "Uniswap V3 DAI/USDC"]
}
print(f"[Agent B - Worker] Deliverable submitted: {mock_deliverable}")

# 3. QA Agent inspects work
print(f"\n[Agent C - Automated QA] Auditing deliverable against specification...")
time.sleep(1)

required_pool_count = 5
actual_pool_count = mock_deliverable.get("pools_analyzed", 0)

if actual_pool_count >= required_pool_count:
    print("✅ [Agent C - QA] Deliverable meets 100% of requirements. Approving full payout...")
    payout_tx = client.complete_task(task_id)
    print(f"🎉 Task Completed! Funds released to Worker. TX: {payout_tx}")
else:
    discrepancy = f"Spec required {required_pool_count} pools, but only {actual_pool_count} delivered."
    print(f"❌ [Agent C - QA] Audit Failed: {discrepancy}")
    print(f"⚖️ [Agent C - QA] Triggering on-chain dispute on Task #{task_id}...")
    
    dispute_tx = client.raise_dispute(
        task_id=task_id,
        evidence_uri=f"ipfs://audit-failure-missing-data"
    )
    print(f"🚨 Dispute Raised! TX: {dispute_tx}")
    print(f"🏛️ Delegated to AgentCourt 3-Agent Jury for autonomous arbitration.")

print("\n" + "=" * 60)
print(f"Simulation finished. View live status on dashboard: http://localhost:8501")
print("=" * 60)
