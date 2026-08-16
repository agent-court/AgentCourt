# ⚖️ AgentCourt: Autonomous Dispute Resolution Protocol on Base

AgentCourt is a decentralized escrow and AI-powered arbitration rail built on Base Mainnet.

## 🌐 On-Chain Infrastructure (Base Mainnet - Chain ID: 8453)
- **Escrow Contract (V2):** `0x7b3a7E51EA2E0832d118b11c4c436b4Cba1b2351`
- **Settlement Asset:** Native Base USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- **Protocol Fee:** 1.50% (150 bps) routed to Treasury
- **Arbitration Engine:** Gemini AI Legal Bench + ChromaDB Vector Embeddings

## 📦 SDK Quickstart
```python
from agentcourt import AgentCourtClient

client = AgentCourtClient(
    private_key="YOUR_PRIVATE_KEY",
    escrow_address="0x7b3a7E51EA2E0832d118b11c4c436b4Cba1b2351"
)
balance = client.get_usdc_balance()
print(f"USDC Balance: ${balance:.2f}")
```
