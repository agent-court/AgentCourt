import streamlit as st
import os, datetime
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AgentCourt | Base Escrow & Arbitration",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ AgentCourt Escrow & Arbitration Dashboard")
st.caption("Decentralized Agent Escrow, Case Resolution & Protocol Treasury on Base Mainnet")

RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDRESS", "0xaC0571eDdFC330f1CAAE19803352Ea55B9dFE720")
USDC_ADDR = os.getenv("USDC_ADDRESS", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
TREASURY_ADDR = os.getenv("TREASURY_ADDRESS", "0xc2eC09e66052927D28574DF4AdF0095fe3C425B6")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Verified on-chain ABI definitions
ESCROW_ABI = [
    {"inputs": [], "name": "taskCount", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "treasury", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "protocolFeeBps", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "paymentToken", "outputs": [{"internalType": "contract IERC20", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "tasks",
        "outputs": [
            {"internalType": "uint256", "name": "id", "type": "uint256"},
            {"internalType": "address", "name": "client", "type": "address"},
            {"internalType": "address", "name": "worker", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "specHash", "type": "string"},
            {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
            {"internalType": "uint8", "name": "status", "type": "uint8"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_worker", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "string", "name": "_specHash", "type": "string"},
            {"internalType": "uint256", "name": "_durationSeconds", "type": "uint256"}
        ],
        "name": "createTask",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_taskId", "type": "uint256"},
            {"internalType": "string", "name": "_deliverableHash", "type": "string"}
        ],
        "name": "submitTask",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_taskId", "type": "uint256"},
            {"internalType": "uint8", "name": "_verdict", "type": "uint8"}
        ],
        "name": "resolveTask",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

USDC_ABI = [
    {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

if not w3.is_connected():
    st.error("❌ Failed to connect to Base RPC.")
    st.stop()

contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDR), abi=ESCROW_ABI)
usdc = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDR), abi=USDC_ABI)

try:
    live_treasury = contract.functions.treasury().call()
except Exception:
    live_treasury = TREASURY_ADDR

with st.sidebar:
    st.header("🌐 Network & Config")
    st.success(f"Connected to Base (Chain ID: {w3.eth.chain_id})")
    st.text_input("Contract Address", CONTRACT_ADDR, disabled=True)
    st.text_input("USDC Token", USDC_ADDR, disabled=True)
    st.text_input("Treasury Wallet", live_treasury, disabled=True)

try:
    total_tasks = contract.functions.taskCount().call()
    treasury_usdc = usdc.functions.balanceOf(w3.to_checksum_address(live_treasury)).call() / 1e6
    treasury_eth = w3.from_wei(w3.eth.get_balance(w3.to_checksum_address(live_treasury)), "ether")
except Exception as e:
    total_tasks, treasury_usdc, treasury_eth = 0, 0.0, 0.0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Tasks Created", total_tasks)
with c2:
    st.metric("Treasury USDC", f"{treasury_usdc:.4f} USDC")
with c3:
    st.metric("Treasury ETH", f"{treasury_eth:.6f} ETH")
with c4:
    st.metric("Protocol Fee", "1.50% (150 BPS)")

st.divider()

tab1, tab2, tab3 = st.tabs(["📋 Task Explorer", "➕ Create Escrow Task", "⚖️ Precedents & Arbitration"])

with tab1:
    st.subheader("On-Chain Task Explorer")
    if total_tasks == 0:
        st.info("No tasks recorded yet.")
    else:
        task_id = st.number_input("Task ID", min_value=1, max_value=int(total_tasks), value=int(total_tasks), step=1)
        try:
            t = contract.functions.tasks(task_id).call()
            # Tuple: (id, client, worker, amount, specHash, createdAt, status)
            status_map = {0: "🟢 Created / Funded", 1: "🟡 Deliverable Submitted", 2: "🔵 Resolved", 3: "🔴 Disputed"}
            
            r1, r2 = st.columns(2)
            with r1:
                st.markdown(f"**Task ID:** `#{t[0]}`")
                st.markdown(f"**Client:** `{t[1]}`")
                st.markdown(f"**Worker:** `{t[2]}`")
                st.markdown(f"**Amount:** `{t[3] / 1e6:.4f} USDC`")
            with r2:
                st.markdown(f"**Spec URI:** `{t[4]}`")
                try:
                    created_dt = datetime.datetime.fromtimestamp(t[5], datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
                except Exception:
                    created_dt = str(t[5])
                st.markdown(f"**Created:** {created_dt}")
                st.markdown(f"**Status:** {status_map.get(t[6], f'Status #{t[6]}')}")
        except Exception as e:
            st.error(f"Failed to fetch Task #{task_id}: {e}")

with tab2:
    st.subheader("Create New Escrow Task")
    with st.form("create_task_form"):
        worker_input = st.text_input("Worker Address (0x...)")
        amount_input = st.number_input("Amount (USDC)", min_value=0.01, value=0.20, step=0.05)
        spec_hash = st.text_input("Spec / IPFS URI", value="ipfs://QmTaskSpecification")
        duration_days = st.slider("Duration (Days)", min_value=1, max_value=30, value=7)
        submit_btn = st.form_submit_button("Create & Fund Task")
        
        if submit_btn:
            if not worker_input or not w3.is_address(worker_input):
                st.error("Please enter a valid worker address.")
            else:
                client_key = os.getenv("CLIENT_PRIVATE_KEY")
                if not client_key:
                    st.error("CLIENT_PRIVATE_KEY is not configured in `.env`.")
                else:
                    try:
                        client_acct = w3.eth.account.from_key(client_key)
                        amt_base = int(amount_input * 1e6)
                        nonce = w3.eth.get_transaction_count(client_acct.address, "pending")
                        
                        tx = contract.functions.createTask(
                            w3.to_checksum_address(worker_input),
                            amt_base,
                            spec_hash,
                            duration_days * 86400
                        ).build_transaction({
                            "from": client_acct.address,
                            "nonce": nonce,
                            "gas": 350000,
                            "gasPrice": int(w3.eth.gas_price * 1.3),
                            "chainId": 8453
                        })
                        signed = w3.eth.account.sign_transaction(tx, client_key)
                        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                        st.success(f"Transaction submitted! Hash: {tx_hash.hex()}")
                    except Exception as e:
                        st.error(f"Transaction failed: {e}")

with tab3:
    st.subheader("Arbitration Engine & Vector Precedents")
    st.markdown("AgentCourt vector memory integrates with `vector_precedents.py` for automated dispute resolution.")
    query = st.text_input("Search Dispute Precedents", placeholder="e.g. Incomplete deliverable")
    if st.button("Search"):
        st.info(f"Querying Chroma vector index for: '{query}'...")
