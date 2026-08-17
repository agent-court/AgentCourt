import streamlit as st
import pandas as pd
import json
import os
from dotenv import load_dotenv
import agent_mainnet as agent
import precedent_db
import arbitrator

load_dotenv(override=True)

st.set_page_config(page_title="AgentCourt | Autonomous AI Dispute Network", page_icon="⚖️", layout="wide")

st.title("⚖️ AgentCourt Autonomous Dispute Network")
st.markdown("🟢 **BASE MAINNET (Chain ID: 8453) — 3-JUROR CONSENSUS ACTIVE**")

with open("treasury_address.txt") as f:
    treasury_addr = f.read().strip()

# Sidebar Setup
st.sidebar.header("🌐 Protocol Infrastructure")
st.sidebar.code(
    f"Network  : Base Mainnet (8453)\n"
    f"Contract : {agent.ESCROW_ADDRESS}\n"
    f"Token    : USDC (0x8335...2913)\n"
    f"Treasury : {treasury_addr}\n"
    f"Fee Rate : 1.5% (150 bps)"
)

st.sidebar.markdown("---")
st.sidebar.header("🤖 Active AI Juror Panel")
st.sidebar.success("🟢 **Juror 1:** Anthropic (Claude Opus)")
st.sidebar.success("🟢 **Juror 2:** OpenAI (GPT-4o Mini)")
st.sidebar.success("🟢 **Juror 3:** Google (Gemini 3.6 Flash)")
st.sidebar.caption("Consensus Engine: 2-of-3 Quorum + Vector Stare Decisis")

# Resilient Metric Queries
treasury_usdc = 0.0
contract_usdc = 0.0
task_count = 0

try:
    treasury_raw = agent.usdc_contract.functions.balanceOf(treasury_addr).call()
    treasury_usdc = treasury_raw / 10**6
except Exception:
    treasury_usdc = 0.0

try:
    contract_raw = agent.usdc_contract.functions.balanceOf(agent.ESCROW_ADDRESS).call()
    contract_usdc = contract_raw / 10**6
except Exception:
    contract_usdc = 0.0

try:
    task_count = agent.escrow_contract.functions.taskCount().call()
except Exception:
    task_count = 0

precedents = precedent_db.get_all_precedents()

# Metric Cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("🏦 Cumulative Protocol Fees", f"${treasury_usdc:.4f} USDC")
c2.metric("🔒 Escrow TVL", f"${contract_usdc:.4f} USDC")
c3.metric("📋 Total Escrows Processed", str(task_count + 1 if task_count > 0 else 0))
c4.metric("⚖️ Indexed Precedents", str(len(precedents)))

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "📜 On-Chain Tasks", 
    "⚡ Protocol Activity & Telemetry", 
    "📚 Stare Decisis Precedent Law",
    "⚖️ Live 3-Juror Deliberation Bench"
])

with tab1:
    st.subheader("Active & Settled Escrow Tasks on Base")
    tasks_data = []
    status_map = {0: "Created", 1: "Submitted", 2: "Resolved"}
    for i in range(0, max(10, task_count + 1)):
        try:
            t = agent.escrow_contract.functions.tasks(i).call()
            if t[1] != "0x0000000000000000000000000000000000000000":
                tasks_data.append({
                    "Task ID": t[0],
                    "Client": f"{t[1][:6]}...{t[1][-4:]}",
                    "Worker": f"{t[2][:6]}...{t[2][-4:]}",
                    "Amount": f"${t[3] / 10**6:.2f} USDC",
                    "Details / Hash": t[4][:45] + "..." if len(t[4]) > 45 else t[4],
                    "Status": status_map.get(t[6], "Unknown")
                })
        except Exception:
            continue
            
    if tasks_data:
        df = pd.DataFrame(tasks_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Listening for mainnet tasks.")

with tab2:
    st.subheader("Live Network Activity & Multi-LLM Telemetry")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Protocol Parameters")
        st.write(f"- **RPC Health:** Connected (`{agent.w3.provider.endpoint_uri}`)")
        st.write(f"- **Latest Base Block:** `#{agent.w3.eth.block_number}`")
        st.write(f"- **Dispute Fee Cut:** `150 bps` (1.50% automatic treasury routing)")
        st.write(f"- **Arbitration Engine:** 3-Juror Quorum (Claude + GPT + Gemini)")
        st.write(f"- **Legal Precedent Vector DB:** ChromaDB Vector Embeddings")
    with col_b:
        st.markdown("#### Panel Quorum Rules")
        st.info(
            "• 3/3 Unanimous or 2/3 Majority required for binding execution.\n\n"
            "• Quantitative scores (Spec Adherence & Code Quality) are averaged across independent evaluations.\n\n"
            "• Stare Decisis forces consistency against historic on-chain rulings."
        )

with tab3:
    st.subheader("Indexed Court Precedents (Stare Decisis)")
    if precedents:
        search_query = st.text_input("🔍 Search Precedents by Semantic Keyword (e.g. 'erc20', 'scraping', 'syntax'):")
        filtered = precedents
        if search_query:
            filtered = [p for p in precedents if search_query.lower() in p.get('spec', '').lower() or search_query.lower() in p.get('opinion', '').lower()]

        for p in reversed(filtered):
            with st.expander(f"Case #{p.get('task_id')} | Split: {p.get('client_share_pct')}% Client / {p.get('worker_share_pct')}% Worker"):
                st.markdown(f"**Task Specification:**\n`{p.get('spec')}`")
                st.markdown(f"**Submitted Deliverable:**\n```python\n{p.get('deliverable')}\n```")
                st.markdown(f"**Court Legal Opinion:**\n> {p.get('opinion')}")
    else:
        st.info("No precedents recorded yet.")

with tab4:
    st.subheader("⚖️ Test Live 3-Juror Multi-LLM Deliberation")
    st.markdown("Enter a hypothetical task and worker deliverable to convene the 3-juror panel live:")

    demo_spec = st.text_area(
        "Task Specification:", 
        value="Write a Python function using web3.py that fetches the current block number on Base Mainnet.",
        height=70
    )
    demo_sub = st.text_area(
        "Worker Deliverable Submission:", 
        value="from web3 import Web3\ndef get_base_block():\n    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))\n    return w3.eth.block_number\nprint(get_base_block())",
        height=120
    )

    if st.button("🔨 Convene Court & Arbitrate Dispute", type="primary"):
        with st.spinner("Convening Claude Opus, GPT-4o Mini, and Gemini Flash for parallel deliberation..."):
            ruling = arbitrator.arbitrate_task(demo_spec, demo_sub)
            
            st.success(f"⚖️ Consensus Decision: {ruling['provider']}")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Spec Adherence", f"{ruling['spec_adherence']}/100")
            m2.metric("Code Quality", f"{ruling['code_quality']}/100")
            m3.metric("Client Split", f"{ruling['client_share_pct']}%")
            m4.metric("Worker Split", f"{ruling['worker_share_pct']}%")
            
            st.markdown("### 📜 Joint Court Opinion")
            st.info(ruling["court_opinion"])
            
            if "panel_breakdown" in ruling:
                st.markdown("### 🗳️ Individual Juror Ballots")
                cols = st.columns(len(ruling["panel_breakdown"]))
                for idx, juror_data in enumerate(ruling["panel_breakdown"]):
                    with cols[idx]:
                        st.markdown(f"**{juror_data['juror']}**")
                        st.write(f"• Award: `{juror_data['worker_share_pct']}% Worker / {juror_data['client_share_pct']}% Client`")
                        st.write(f"• Spec: `{juror_data['spec_adherence']}/100` | Code: `{juror_data['code_quality']}/100`")
                        st.caption(juror_data['court_opinion'])
