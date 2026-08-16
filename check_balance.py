from agentcourt import AgentCourtClient
from dotenv import dotenv_values

cfg = dotenv_values(".env.mainnet")
with open("mainnet_escrow_address.txt") as f:
    addr = f.read().strip()

client = AgentCourtClient(private_key=cfg["PRIVATE_KEY"], escrow_address=addr)
bal = client.get_usdc_balance()

print("==================================================")
print(f"Deployer Wallet : {client.address}")
print(f"USDC on Base    : ${bal:.4f} USDC")
print("==================================================")
