# AgentCourt (V5) ⚖️
**Decentralized, Deterministic AI Arbitration Protocol on Base**

AgentCourt is an institutional settlement infrastructure designed for autonomous agent commerce.

---

## 🏗️ Protocol Architecture

- `AgentEscrowV5`: Production USDC escrow contract on Base with basis-points (BPS) allocation.
- `vector_precedents.py`: Persistent ChromaDB semantic case law memory (*Machine Stare Decisis*).
- `arbitrator.py`: Multi-LLM jury panel (Gemini, GPT-4o, Claude) running at zero-temperature with deterministic median BPS quorum.
- `daemon_v3.py`: Automated event listener and on-chain resolution executor.

---

## 🔰 State Machine Invariants

`Created` → `Funded` → `Started` → `Completed` → `Disputed` → `Settled`
- No unilateral bypasses or reversible states.
- Every dispute resolution commits a `bytes32 verdictHash` on-chain.

---

## ✅ Live Demo & Simulation

Run the 60-second agent-to-agent direct dispute and settlement simulation:

```bash
python scripts/simulate_dispute.py
```
