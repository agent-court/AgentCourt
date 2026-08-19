import os
from dotenv import load_dotenv

load_dotenv()

from sdk.agentcourt.client import AgentCourtClient

DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
if not DEPLOYER_KEY:
    raise ValueError("Please set DEPLOYER_PRIVATE_KEY in your .env file.")

# 1. Initialize Client
client = AgentCourtClient(private_key=DEPLOYER_KEY)
contractor_wallet = "0xAe679030eD87b126B726A3e7d73e58e633465d76"

print("🤖 [Client Agent] Initializing AgentCourt Client...")
print(f"🔗 Connected to contract: {client.contract_address}")

# 2. Lock 0.0001 ETH in escrow
print("\n💼 [Step 1] Creating Escrow Task for Contractor Agent...")
create_tx, task_id = client.create_task(
    contractor=contractor_wallet,
    spec_uri="ipfs://dataset-crawler-spec-v1",
    amount_eth=0.0001,
    challenge_period=300 # 5-minute challenge window
)
print(f"✅ Escrow Task #{task_id} Created! TX: {create_tx}")

# 3. Read Task State
task_data = client.get_task(task_id)
print(f"\n📋 [Step 2] Verified On-Chain State for Task #{task_id}:")
print(f" - Client: {task_data['client']}")
print(f" - Contractor: {task_data['contractor']}")
print(f" - Amount: {task_data['amount_eth']} ETH")
print(f" - Status: {task_data['status']} (0 = Created)")

# 4. Trigger Dispute
print(f"\n⚖️ [Step 3] Client raises dispute on Task #{task_id}...")
dispute_tx = client.raise_dispute(task_id)
print(f"🚨 Dispute Raised! TX: {dispute_tx}")
print(f"👀 Check Daemon Tab: The autonomous jury will deliberate Task #{task_id}.")
