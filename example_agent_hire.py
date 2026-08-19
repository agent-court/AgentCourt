import os
import time
from dotenv import load_dotenv

load_dotenv()

from sdk.agentcourt.client import AgentCourtClient

DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
if not DEPLOYER_KEY:
    raise ValueError("Please set DEPLOYER_PRIVATE_KEY in your .env file.")

# 1. Initialize client
client = AgentCourtClient(private_key=DEPLOYER_KEY)
contractor_wallet = "0xAe679030eD87b126B726A3e7d73e58e633465d76"

print("🤖 [Client Agent] Initializing AgentCourt Client...")
print(f"🔗 Connected to contract: {client.contract_address}")

# 2. Create a new task (Task #15)
print("\n💼 [Step 1] Locking funds in escrow for Contractor Agent...")
tx_hash = client.create_task(
    contractor=contractor_wallet,
    spec_uri="ipfs://dataset-crawler-spec-v1",
    amount_eth=0.0001,
    challenge_period=300
)
print(f"✅ Escrow Created! TX: {tx_hash}")

# 3. Retrieve newest task ID
task_id = client.contract.functions.taskCounter().call()
task_data = client.get_task(task_id)

print(f"\n📋 [Step 2] Retrieved On-Chain Task #{task_id}:")
print(f" - Client: {task_data['client']}")
print(f" - Contractor: {task_data['contractor']}")
print(f" - Amount: {task_data['amount_eth']} ETH")
print(f" - Status: {task_data['status']} (0 = Created)")

# 4. Contractor submits work
print("\n⚙️ [Step 3] Submitting task deliverable...")
submit_tx = client.submit_work(task_id)
print(f"✅ Work Submitted! TX: {submit_tx}")

# 5. Client raises dispute
print("\n⚖️ [Step 4] Client raises dispute for autonomous jury review...")
dispute_tx = client.raise_dispute(task_id)
print(f"🚨 Dispute Raised! TX: {dispute_tx}")
print(f"👀 Check Daemon Tab: The autonomous jury will deliberate Task #{task_id}.")
