import os
import time
from sdk.agentcourt.client import AgentCourtClient

# Load configuration
DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
if not DEPLOYER_KEY:
    raise ValueError("Please set DEPLOYER_PRIVATE_KEY in your environment or .env file.")

# 1. Initialize the client
client = AgentCourtClient(private_key=DEPLOYER_KEY)
contractor_wallet = "0x4c67A8333D7203b879C5C6fF353dC1D9eEcB5d76"

print("🤖 [Client Agent] Initializing AgentCourt Client...")
print(f"🔗 Connected to contract: {client.contract_address}")

# 2. Client Agent locks 0.0001 ETH in escrow for a data scraping task
print("\n💼 [Step 1] Locking funds in escrow for Contractor Agent...")
tx_hash = client.create_task(
    contractor=contractor_wallet,
    spec_uri="ipfs://dataset-crawler-spec-v1",
    amount_eth=0.0001,
    challenge_period=300 # 5-minute challenge window for testing
)
print(f"✅ Escrow Created! TX: {tx_hash}")

# 3. Retrieve on-chain task details
task_id = client.contract.functions.taskCounter().call()
task_data = client.get_task(task_id)

print(f"\n📋 [Step 2] Retrieved On-Chain Task #{task_id}:")
print(f" - Client: {task_data['client']}")
print(f" - Contractor: {task_data['contractor']}")
print(f" - Amount: {task_data['amount_eth']} ETH")
print(f" - Status: {task_data['status']} (0 = Created)")

# 4. Contractor submits partial or disputed deliverable
print("\n⚙️ [Step 3] Simulating Contractor work submission...")
submit_tx = client.submit_task(task_id)
print(f"✅ Task Submitted! TX: {submit_tx}")

# 5. Client raises a dispute (triggers the autonomous 3-agent jury)
print("\n⚖️ [Step 4] Client finds discrepancies and triggers dispute...")
dispute_tx = client.raise_dispute(task_id)
print(f"🚨 Dispute Raised! TX: {dispute_tx}")
print(f"👀 Autonomous Daemon will now convene the jury and propose an on-chain ruling.")
