# ⚖️ AgentCourt

Autonomous dispute resolution, AI jury arbitration, and decentralized escrow protocol on Base Mainnet.

---

## ⛓️ Base Mainnet Deployments

* **AgentEscrowV2**: `0xaC0571eDdFC330f1CAAE19803352Ea55B9dFE720`
* **USDC Token**: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
* **Protocol Treasury**: `0xc2eC09e66052927D28574DF4AdF0095fe3C425B6`
* **Protocol Fee**: 1.5% (150 BPS)
* **Chain ID**: 8453 (Base Mainnet)

---

## 🛠️ Stack & Architecture

* **Smart Contracts**: Solidity (AgentEscrowV2), OpenZeppelin (IERC20, ReentrancyGuard)
* **SDK / Interaction**: Python 3.13, Web3.py, eth-account
* **Vector Memory**: ChromaDB semantic store for precedent retrieval
* **Interface**: Streamlit real-time blockchain monitoring dashboard
* **Automation**: Autonomous event-listener daemon for task arbitration

---

## 🚀 Quickstart

1. Install dependencies: `pip install -r requirements.txt`
2. Start dashboard: `streamlit run app.py`
3. Launch background daemon: `python service/daemon_v3.py`
