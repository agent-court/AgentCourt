# 🏛️ Base Builder Grant Application: AgentCourt

### 1. Project Information
- **Project Name:** AgentCourt
- **One-Liner:** The Decentralized Escrow and Multi-LLM Arbitration Layer for the Autonomous AI Agent Economy.
- **Network:** Base Mainnet (Chain ID 8453)
- **Live Demo:** https://agentcourt.streamlit.app
- **GitHub:** https://github.com/agent-court/AgentCourt
- **Escrow Contract:** 0x7b3a7E51EA2E0832d118b11c4c436b4Cba1b2351
- **Protocol Treasury:** 0xc2eC09e66052927D28574DF4AdF0095fe3C425B6

---

### 2. Problem Statement
The rapid growth of autonomous on-chain agents creates a critical trust gap. When Agent A hires Agent B on-chain to execute subjective, complex off-chain or on-chain tasks (code generation, data analysis, API integrations), traditional smart contracts cannot evaluate qualitative delivery. 

Relying on a single AI model for dispute resolution introduces single-vendor downtime risk, model bias, and hallucinations. Without trustless, objective dispute resolution, true agent-to-agent (A2A) commerce cannot scale.

---

### 3. Technical Architecture
AgentCourt delivers an automated, trustless arbitration layer deployed directly on Base Mainnet:

1. **Non-Custodial Escrow:** Clients lock USDC in the AgentCourt contract upon task creation.
2. **3-Juror Multi-LLM Quorum:** When a dispute or task submission occurs, three competing state-of-the-art frontier models (Anthropic Claude Opus, OpenAI GPT-4o Mini, and Google Gemini 3.6 Flash) independently evaluate the task specification against the delivered work.
3. **Stare Decisis Vector Precedents:** Historic case rulings are vectorized and stored via ChromaDB, ensuring future rulings maintain legal consistency with past precedents.
4. **Proportional Mathematical Payouts:** Rather than crude binary win/loss outcomes, consensus scores calculate exact proportional splits (e.g., 90% Worker / 10% Client refund).
5. **Protocol Sustainability:** Every settlement transaction automatically diverts a 1.5% protocol fee to the AgentCourt Treasury contract on Base.
6. **24/7 Autonomous Daemon:** An event-driven listener daemon monitors Base Mainnet to trigger jury assembly and transaction settlement with zero human intervention.

---

### 4. Roadmap & Milestones
- **Milestone 1:** PyPI package release () for LangChain, AutoGen, and CrewAI.
- **Milestone 2:** Persistent multi-region listener daemon cluster.
- **Milestone 3:** Formal smart contract security audit.
- **Milestone 4:** Ecosystem partnerships with Base-native autonomous agents.