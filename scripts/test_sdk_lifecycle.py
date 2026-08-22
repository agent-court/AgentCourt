import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from agentcourt import AgentCourtClient

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
if not PRIVATE_KEY:
    print("❌ Error: PRIVATE_KEY or ARBITRATOR_PRIVATE_KEY not set in .env")
    sys.exit(1)

client = AgentCourtClient(private_key=PRIVATE_KEY)
caller_addr = client.account.address

print("=" * 60)
print("🤖 AgentCourt SDK — End-to-End Lifecycle Verification")
print("=" * 60)
print(f"👤 Connected Signer: {caller_addr}")
print(f"🏛️ Escrow Contract: {client.contract_address}")

# 1. Create Task via SDK
spec = "Decentralized Liquidity Monitor with Subgraph sync & Prometheus metrics."
print("\n1️⃣  Creating task via AgentCourtClient.create_task()...")
task_id = client.create_task(
    worker_address=caller_addr,
    amount_usdc=0,
    spec_text=spec
)
print(f"   ✅ Created Task #{task_id}")

# 2. Fund Task via SDK
print(f"\n2️⃣  Funding task #{task_id} via AgentCourtClient.fund_task()...")
receipt_fund = client.fund_task(task_id)
print(f"   ✅ Funded (Tx: {receipt_fund['tx_hash'][:14]}... | Block #{receipt_fund['blockNumber']})")

# 3. Start Task via SDK
print(f"\n3️⃣  Starting task #{task_id} via AgentCourtClient.start_task()...")
receipt_start = client.start_task(task_id)
print(f"   ✅ Started (Tx: {receipt_start['tx_hash'][:14]}... | Block #{receipt_start['blockNumber']})")

# 4. Trigger Dispute via SDK
print(f"\n4️⃣  Opening dispute on task #{task_id} via AgentCourtClient.open_dispute()...")
receipt_disp = client.open_dispute(task_id)
print(f"   ⚡ Dispute broadcasted! (Tx: {receipt_disp['tx_hash'][:14]}... | Block #{receipt_disp['blockNumber']})")

# 5. Verify Updated Task State
task_info = client.get_task(task_id)
print(f"\n📊 Task #{task_id} Current State: {task_info['state']}")
print("=" * 60)
print("👉 Monitor your daemon_v3 terminal for multi-model jury deliberation & on-chain settlement.")
print("=" * 60)
