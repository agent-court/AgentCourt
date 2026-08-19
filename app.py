import os
import json
import time
import streamlit as st
import pandas as pd
from web3 import Web3

st.set_page_config(page_title="AgentCourt V3 | Autonomous Protocol", page_icon="⚖️", layout="wide")

RPC_URL = os.getenv("BASE_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
ESCROW_RAW = os.getenv("ESCROW_V3_ADDRESS", "0x4a1629907Aa583E0f24EA66929f3D38410c66cf2")
ESCROW_ADDRESS = Web3.to_checksum_address(ESCROW_RAW)

STATUS_MAP = {
    0: ("Created", "🔵"),
    1: ("Submitted", "🟡"),
    2: ("Resolved", "🟢"),
    3: ("Disputed", "🔴"),
    4: ("Ruling Proposed", "⚖️"),
    5: ("Refunded", "⚪")
}

@st.cache_resource
def get_contract():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    artifact_path = "contracts/AgentEscrowV3_abi.json" if os.path.exists("contracts/AgentEscrowV3_abi.json") else "agentcourt/contracts/AgentEscrowV3_abi.json"
    with open(artifact_path, "r") as f:
        abi = json.load(f)
    return w3, w3.eth.contract(address=ESCROW_ADDRESS, abi=abi)

w3, contract = get_contract()

st.title("⚖️ AgentCourt V3 — Autonomous Escrow & Arbitration")
st.caption(f"Connected to Base Sepolia | Contract: `{ESCROW_ADDRESS}`")

# 1. Fetch Task Counter
try:
    total_tasks = contract.functions.taskCounter().call()
except Exception as e:
    total_tasks = 0
    st.error(f"Error connecting to contract: {e}")

court_signer = os.getenv("DEPLOYER_PUBLIC_KEY", "0x7807d927C720bdEE226AbaC41E0793326c5b62c6")

col1, col2, col3 = st.columns(3)
col1.metric("Total Protocol Tasks", total_tasks)
col2.metric("Court Signer", f"{court_signer[:6]}...{court_signer[-4:]}")
col3.metric("Network Status", "Base Sepolia (Live)")

st.divider()
st.subheader("📋 Active Protocol Tasks")

if total_tasks == 0:
    st.info("No tasks created yet on Base Sepolia.")
else:
    task_rows = []
    current_time = int(time.time())

    for task_id in range(total_tasks, 0, -1):
        try:
            # struct: [id, client, contractor, amount, specURI, challengePeriod, status, proposedBps, proposedAt, rulingURI]
            t = contract.functions.tasks(task_id).call()
            status_code = t[6]
            status_name, status_icon = STATUS_MAP.get(status_code, ("Unknown", "⚪"))
            
            challenge_remaining = "—"
            if status_code == 4 and t[8] > 0:
                remaining_sec = (t[8] + t[5]) - current_time
                challenge_remaining = f"{max(0, remaining_sec // 60)} min left" if remaining_sec > 0 else "Expired (Ready to Settle)"

            task_rows.append({
                "Task ID": f"#{t[0]}",
                "Status": f"{status_icon} {status_name}",
                "Amount (ETH)": f"{Web3.from_wei(t[3], 'ether'):.4f}",
                "Proposed Split": f"{t[7]/100}% Client / {100 - (t[7]/100)}% Contractor" if status_code == 4 else "—",
                "Challenge Window": challenge_remaining,
                "Client": f"{t[1][:6]}...{t[1][-4:]}",
                "Contractor": f"{t[2][:6]}...{t[2][-4:]}",
                "Spec URI": t[4]
            })
        except Exception as e:
            continue

    if task_rows:
        df = pd.DataFrame(task_rows)
        st.dataframe(df, use_container_width=True)

st.divider()
st.subheader("🔍 Case Law & Precedent Log")
st.caption("Autonomous Jury deliberation history and on-chain rulings")

st.markdown("""
* **Task #14:** 60% Client / 40% Contractor | *Status: ⚖️ Ruling Proposed* | [View BaseScan TX](https://sepolia.basescan.org/tx/0x627f7cde17bfdc724090c1cac56f35e79c36adb2f927e0a5b977e4e257f35484)
* **Contract:** Verified Source Code | [View on BaseScan](https://sepolia.basescan.org/address/0x4a1629907Aa583E0f24EA66929f3D38410c66cf2#code)
""")
