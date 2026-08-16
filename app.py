import json
import time
import pandas as pd
import streamlit as st
import agent_mainnet as agent
import precedent_db

st.set_page_config(
    page_title="AgentCourt | Live on Base Mainnet",
    page_icon="⚖️",
    layout="wide"
)

# Header
st.title("⚖️ AgentCourt Autonomous Dispute Network")
st.markdown("🟢 **BASE MAINNET (Chain ID: 8453) — PRODUCTION ACTIVE**")

with open("treasury_address.txt") as f:
    treasury_addr = f.read().strip()

st.sidebar.header("🌐 Protocol Infrastructure")
st.sidebar.code(
    f"Network  : Base Mainnet (8453)\n"
    f"Contract : {agent.ESCROW_ADDRESS}\n"
    f"Token    : USDC (0x8335...2913)\n"
    f"Treasury : {treasury_addr}\n"
    f"Fee Rate : 1.5% (150 bps)"
)

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
c3.metric("📋 Total Escrows Processed", str(task_count))
c4.metric("⚖️ Indexed Precedent Case Law", str(len(precedents)))

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📜 On-Chain Tasks", "⚡ Protocol Activity & Event Pulse", "📚 Stare Decisis Precedent Case Law"])

with tab1:
    st.subheader("Active & Settled Escrow Tasks")
    if task_count > 0:
        tasks_data = []
        status_map = {0: "Created", 1: "Submitted", 2: "Resolved"}
        for i in range(1, task_count + 1):
            try:
                t = agent.escrow_contract.functions.tasks(i).call()
                tasks_data.append({
                    "Task ID": t[0],
                    "Client": f"{t[1][:6]}...{t[1][-4:]}",
                    "Worker": f"{t[2][:6]}...{t[2][-4:]}",
                    "Amount": f"${t[3] / 10**6:.2f} USDC",
                    "Details / Hash": t[4][:40] + "..." if len(t[4]) > 40 else t[4],
                    "Status": status_map.get(t[6], "Unknown")
                })
            except Exception:
                continue
        df = pd.DataFrame(tasks_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No mainnet tasks created yet. Escrow contract is listening for agent transactions.")

with tab2:
    st.subheader("Live Network Activity & Telemetry")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Protocol Telemetry")
        st.write(f"- **RPC Health:** Connected (`{agent.w3.provider.endpoint_uri}`)")
        st.write(f"- **Latest Base Block:** `#{agent.w3.eth.block_number}`")
        st.write(f"- **Dispute Fee Cut:** `150 bps` (1.50% automatic treasury routing)")
        st.write(f"- **Arbitration Model:** Gemini AI Legal Engine + ChromaDB Vector Embeddings")
    with col_b:
        st.markdown("#### Recent Contract Events")
        st.info("Event listener synced with Base Mainnet. Live block emissions will log here.")

with tab3:
    st.subheader("Indexed Court Precedents (Stare Decisis)")
    if precedents:
        search_query = st.text_input("🔍 Search Precedents by Semantic Keyword (e.g. 'scraping', 'syntax', 'caching'):")
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
