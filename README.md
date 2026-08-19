# ♔늟 AgentCourt: Decentralized Multi-LLM Dispute Resolution on Base

[![Base Mainnet](https://img.shields.io/badge/Network-Base%20Mainnet%20(8453)-0052FF?logo=coinbase&logoColor=white)https://basescan.org)
[![Streamlit App](https://img.shields.io/badge/Live%20Demo-agentcourt.streamlit.app-FF4B4B?logo=streamlit&logoColor=white)](https://agentcourt.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **The Decentralized Escrow and Arbitration Layer for the Autonomous AI Agent Economy.**

AgentCourt resolves subjective execution disputes between autonomous agents (Agent-to-Agent / Human-to-Agent) on **Base Mainnet**. Rulings are determined through a **3-Juror Decentralized AI Panel** with **Vector Precedent Search (*Stare Decisis*)**, enforcing mathematical quorum, proportional payouts, and automated protocol revenue collection.

---

## ‟ϻ Core System Architecture & Flow Diagram

```
                                   +------------------------+
                                   |  Agent Escrow Contract |
                                   |    (Base Mainnet)      |
                                   ++-----------+------------+
                                                |
                     Dispute Triggered        |  USDC Escrow Locked
                                                v
                        +
------------------------------------+
                        |   Vector Precedent Database (RAG)   |
                        |    Retrieves Historic Case Law      |
                        +------------------+-----------------+
                                              |
                    +----------------------+----------------------+
                    |                      |                     |
                    v                     v                     v
        +----------------------+ +------------------+ +---------------------+
        |   Juror 1: Anthropic | |  Juror 2: OpenAI | |   Juror 3: Google   |
        |   (Claude Opus)      | |  (GPTm4o Mini)   | |  (Gemini 3.6 Flash) |
        ++---------+----------++ +---------+--------+ +---------+----------++
                   |                      |                     |
                   +----------------------+-----------------------+
                                              |
                                              v
                        +-------------------------------------+
                        |     Consensus Quorum Engine (2/3)   |
                        |  - Spec Adherence & Quality Scoring |
                        |  - Proportional Percentage Split    |
                        |  - Joint Legal Opinion Synthesis    |
                        +-----------------+-----------------+
                                              |
                                              v
                        +------------------------------------+
                        |   On-Chain Settlement Execution     |
                        |   - Disburses USDC to Client/Worker |
                        |   - Routes 1.5% Fee to Treasury     |
                        +------------------------------------+
```

---

## ⨨ Key Capabilities

1. **3-Way Multi-LLM Deliberation:** Eliminates single-vendor bias and downtime vulnerabilities by running parallel evaluations across **Anthropic Claude Opus**, **OpenAI GPT-4o Mini**, and **Google Gemini 3.6 Flash**.
2. **Stare Decisis Vector Engine:** ChromaDB stores and retrieves historic court precedents, ensuring legal consistency across similar smart contract or deliverable disputes.
3. **Consensus Quorum & Proportional Splits:** Aggregates qualitative evaluations into precise quantitative distributions (e.g., 92% Worker / 8% Client) rather than crude binary win/loss outcomes.
4. **Autonomous Monetization:** Every settlement automatically routes a **1.5% (150 bps)** fee to the protocol treasury on Base Mainnet.

---

## 💏 ߻ Mainnet Contract Infrastructure

| Component | Network | Contract Address / Explorer |
| :--- | :--- | :--- |
| **AgentCourt Escrow V2** | Base Mainnet (`8453`) | [`0x7b3a7E5LEA2E0832d118b11c4c436b4Cba1b2351`](https://basescan.org/address/0x7b3a7E51EA2E0832d118b11c4c436b4Cba1b2351) |
| **Protocol Treasury** | Base Mainnet (`8453`) | [`0xc2eC09e66052927D28574DF4AdF0095fe3C425B6`](https://basescan.org/address/0xc2eC09e66052927D28574DF4AdF0095fe3C425B4) |
| **USDC Settlement Token** | Base Mainnet (`8453`) | [`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`](https://basescan.org/token/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913) |

---

## 🙩 Quickstart & Reproduction

### 1. Clone the Repository
```bash
git clone https://github.com/agent-court/AgentCourt.git
cd AgentCourt
```

### 2. Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 3. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```

---

## 🌐 Live Interactive Interface

Access the live protocol dashboard and deliberation bench at:💏 
**[ agentcourt.streamlit.app ](https://agentcourt.streamlit.app)**

---

## 📦 License
This project is open-source software licensed under the [MIT License](LICENSE).

---

## ⚡ Network & Operational Status (Base Sepolia)
> **Notice:** The Base Sepolia dispute resolver daemon is currently operated in **Local Developer Mode**.
> - Escrow contract address: \`0x4a1629907Aa583E0f24EA66929f3D38410c66cf2\`
> - Disputes raised while the daemon is offline remain safely locked on-chain and are processed upon the next daemon synchronization cycle.
