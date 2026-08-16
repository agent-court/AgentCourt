from dotenv import dotenv_values

existing = dotenv_values(".env")

pk = existing.get("PRIVATE_KEY", "").strip()
gemini = existing.get("GEMINI_API_KEY", "").strip()

mainnet_env = f"""PRIVATE_KEY={pk}
RPC_URL=https://mainnet.base.org
CHAIN_ID=8453
GEMINI_API_KEY={gemini}
"""

with open(".env.mainnet", "w") as f:
    f.write(mainnet_env)

print("✅ .env.mainnet created automatically from your existing .env keys!")
