from agentcourt import AgentCourtClient
from dotenv import dotenv_values

cfg = dotenv_values(".env.mainnet")
with open("mainnet_escrow_address.txt") as f:
    addr = f.read().strip()

client = AgentCourtClient(private_key=cfg["PRIVATE_KEY"], escrow_address=addr)

print("==================================================")
print("🤖 AGENTCOURT SDK VERIFICATION")
print(f"Client Address : {client.address}")
print(f"Escrow Contract: {client.escrow_address}")
print(f"Total Tasks    : {client.get_total_tasks()}")
print("==================================================")
print("✅ AgentCourt SDK loaded and connected successfully to Base Mainnet!")
