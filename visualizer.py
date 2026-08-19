import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
from dotenv import load_dotenv

from agentcourt.client import AgentCourtClient
from agentcourt.vector_precedents import find_relevant_precedents

load_dotenv()

app = FastAPI(title="AgentCourt Command Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RPC_URL = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
CONTRACT_ADDRESS = os.getenv("ESCROW_CONTRACT_V4", "0x0233B2B49788204ddd00Fb39508b944aC3904F71")
DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
checksum_address = Web3.to_checksum_address(CONTRACT_ADDRESS)

# ABI for reading count and resolving
ABI = [
    {
        "inputs": [],
        "name": "jobCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_jobId", "type": "uint256"},
            {"internalType": "uint256", "name": "_workerBasisPoints", "type": "uint256"}
        ],
        "name": "resolveJob",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=checksum_address, abi=ABI)

STATE_MAP = {
    0: "Open",
    1: "Funded",
    2: "Submitted",
    3: "Terminal"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentCourt Command Center</title>
  <style>
    :root {
      --bg: #07090e;
      --card: #0d1117;
      --border: #21262d;
      --text: #f0f6fc;
      --muted: #8b949e;
      --cyan: #38bdf8;
      --green: #3fb950;
      --yellow: #eab308;
      --purple: #a855f7;
      --red: #f87171;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      padding: 2.5rem 1rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .wrapper {
      max-width: 960px;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .header-left h1 {
      font-size: 1.6rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .header-left p {
      font-size: 0.85rem;
      color: var(--muted);
      margin-top: 0.25rem;
    }
    .header-left a {
      color: var(--cyan);
      text-decoration: none;
      font-family: ui-monospace, monospace;
    }
    .badge {
      font-size: 0.75rem;
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      background: #161b22;
      border: 1px solid var(--border);
      color: var(--cyan);
      font-family: ui-monospace, monospace;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .section-title {
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--cyan);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    textarea {
      width: 100%;
      height: 65px;
      background: #161b22;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.6rem;
      border-radius: 4px;
      font-family: inherit;
      resize: vertical;
      font-size: 0.85rem;
    }
    .btn {
      background: var(--cyan);
      color: #07090e;
      border: none;
      padding: 0.65rem 1.25rem;
      font-weight: 700;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.85rem;
      transition: opacity 0.15s ease;
    }
    .btn-sm {
      padding: 0.3rem 0.6rem;
      font-size: 0.72rem;
      font-weight: 600;
      border-radius: 3px;
    }
    .btn-settle {
      background: var(--green);
      color: #07090e;
    }
    .btn:hover { opacity: 0.9; }
    .table-container {
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
      text-align: left;
    }
    th {
      padding: 0.6rem 0.75rem;
      background: #161b22;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      font-weight: 600;
    }
    td {
      padding: 0.75rem;
      border-bottom: 1px solid var(--border);
      font-family: ui-monospace, monospace;
    }
    tr.clickable-row {
      cursor: pointer;
      transition: background 0.15s ease;
    }
    tr.clickable-row:hover {
      background: #161b22;
    }
    .status-pill {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.4rem;
      border-radius: 3px;
      display: inline-block;
      text-transform: uppercase;
    }
    .status-Open { background: #1e293b; color: var(--cyan); }
    .status-Funded { background: #3b2c04; color: var(--yellow); }
    .status-Submitted { background: #2e1065; color: var(--purple); }
    .status-Terminal { background: #064e3b; color: var(--green); }
    .juror-card {
      border: 1px solid var(--border);
      background: #161b22;
      border-radius: 6px;
      padding: 0.85rem;
      margin-top: 0.5rem;
      font-size: 0.82rem;
      line-height: 1.45;
    }
    .juror-card-header {
      font-weight: 700;
      color: var(--purple);
      margin-bottom: 0.35rem;
      display: flex;
      justify-content: space-between;
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="header-left">
        <h1>🏛️ AgentCourt Command Center</h1>
        <p>Connected to Base Sepolia • Contract: <a href="https://sepolia.basescan.org/address/0x0233B2B49788204ddd00Fb39508b944aC3904F71" target="_blank">0x0233...4F71</a></p>
      </div>
      <div class="badge">ERC-8183 Protocol Live</div>
    </div>

    <!-- Deliberation Engine -->
    <div class="card">
      <div class="section-title">⚡ Synthetic Jury Deliberation Engine</div>
      <div style="display:flex; gap:1rem; align-items:center;">
        <label style="font-size:0.75rem; color:var(--muted)">Target On-Chain Job ID:</label>
        <input type="number" id="targetJobId" value="3" style="width:70px; background:#161b22; border:1px solid var(--border); color:var(--text); padding:0.25rem 0.5rem; border-radius:4px; font-family:monospace;">
      </div>

      <label style="font-size:0.75rem; color:var(--muted)">Task Specification</label>
      <textarea id="taskSpec">Build a Python script connecting to Uniswap V3 on Base and executing a token swap.</textarea>
      
      <label style="font-size:0.75rem; color:var(--muted)">Delivered Evidence</label>
      <textarea id="evidence">Script delivered with valid ABI and routing logic, but slippage parameters were hardcoded instead of dynamic.</textarea>
      
      <div style="display:flex; gap:0.75rem; align-items:center;">
        <button class="btn" onclick="runDeliberation()">⚡ Convene Synthetic Jury</button>
        <span id="settleStatus" style="font-size:0.8rem;"></span>
      </div>

      <div id="deliberationOutput" style="display:none; margin-top:0.5rem; border-top:1px solid var(--border); padding-top:1rem;"></div>
    </div>

    <!-- On-Chain Registry -->
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div class="section-title">📋 Live On-Chain Escrow Registry</div>
        <button class="btn btn-sm" onclick="loadEscrows()" style="background:#161b22; color:var(--text); border:1px solid var(--border);">🔄 Refresh Ledger</button>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Status</th>
              <th>Escrow Amount</th>
              <th>Client</th>
              <th>Worker</th>
              <th>Payout Split</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="escrowTableBody">
            <tr><td colspan="7" style="color:var(--muted); text-align:center;">Loading active escrow jobs from Base Sepolia...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    let lastCalculatedBps = null;

    async function runDeliberation() {
      const out = document.getElementById('deliberationOutput');
      out.style.display = 'block';
      out.innerHTML = '<span style="color:var(--cyan); font-size:0.85rem;">⏳ Retrieving ChromaDB precedents and convening AI jurors...</span>';

      try {
        const res = await fetch('/api/deliberate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            task_spec: document.getElementById('taskSpec').value,
            evidence: document.getElementById('evidence').value
          })
        });
        const data = await res.json();
        
        const workerPct = Number(data.worker_share_pct);
        const clientPct = Number(data.client_share_pct);
        lastCalculatedBps = Math.round(workerPct * 100);

        let html = `
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
            <h3 style="font-size:1rem;">Consensus Verdict: <span style="color:var(--green)">${workerPct}% Worker / ${clientPct}% Client</span></h3>
            <div style="display:flex; gap:0.5rem; align-items:center;">
              <span class="badge">${lastCalculatedBps} BPS</span>
              <button class="btn btn-sm btn-settle" onclick="executeSettlement()">⛓️ Settle On-Chain</button>
            </div>
          </div>
        `;

        if (data.precedents && data.precedents.length > 0) {
          html += '<h4 style="margin-top:0.85rem; color:var(--cyan); font-size:0.8rem;">📚 ChromaDB Precedents Cited:</h4>';
          data.precedents.forEach(p => {
            html += `<div style="font-size:0.8rem; color:var(--muted); margin-top:0.25rem;">• <strong>Case #${p.case_id} (${p.title})</strong>: Established ${p.ruling_basis_points} BPS (${p.ruling_basis_points/100}%).</div>`;
          });
        }

        html += '<h4 style="margin-top:0.85rem; color:var(--purple); font-size:0.8rem;">⚖️ Synthetic Juror Deliberations:</h4>';
        const opinions = data.court_opinion.split(' | ');
        opinions.forEach((op, idx) => {
          html += `
            <div class="juror-card">
              <div class="juror-card-header">
                <span>Juror #${idx + 1}</span>
                <span>Deliberation Log</span>
              </div>
              <div style="color:var(--muted);">${op}</div>
            </div>
          `;
        });

        out.innerHTML = html;
      } catch (err) {
        out.innerHTML = '<span style="color:var(--red); font-size:0.85rem;">Error executing deliberation. Check terminal log.</span>';
      }
    }

    async function executeSettlement(jobIdParam = null, bpsParam = null) {
      const targetId = jobIdParam || document.getElementById('targetJobId').value;
      const targetBps = bpsParam !== null ? bpsParam : (lastCalculatedBps || 7000);
      const statusSpan = document.getElementById('settleStatus');

      statusSpan.innerHTML = `<span style="color:var(--cyan);">Submitting settlement tx for Job #${targetId}...</span>`;

      try {
        const res = await fetch('/api/settle', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ job_id: Number(targetId), basis_points: Number(targetBps) })
        });
        const result = await res.json();
        
        if (result.status === "success") {
          statusSpan.innerHTML = `<span style="color:var(--green);">✅ Settled! Tx: <a href="https://sepolia.basescan.org/tx/${result.tx_hash}" target="_blank" style="color:var(--cyan);">${result.tx_hash.substring(0, 10)}...</a></span>`;
          loadEscrows();
        } else {
          statusSpan.innerHTML = `<span style="color:var(--red);">❌ Settlement Failed: ${result.error}</span>`;
        }
      } catch (e) {
        statusSpan.innerHTML = `<span style="color:var(--red);">❌ RPC Error submitting transaction.</span>`;
      }
    }

    function selectJob(id) {
      document.getElementById('targetJobId').value = id;
    }

    async function loadEscrows() {
      const tbody = document.getElementById('escrowTableBody');
      try {
        const res = await fetch('/api/jobs');
        const jobs = await res.json();
        if (!jobs || jobs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7" style="color:var(--muted); text-align:center;">No escrow jobs found.</td></tr>';
          return;
        }
        let html = '';
        jobs.forEach(j => {
          const shortClient = j.client.substring(0, 6) + '...' + j.client.substring(j.client.length - 4);
          const shortWorker = j.worker.substring(0, 6) + '...' + j.worker.substring(j.worker.length - 4);
          const split = j.state === 'Terminal' ? `${j.worker_basis_points / 100}% Worker / ${100 - (j.worker_basis_points / 100)}% Client` : 'Pending';
          
          let actionBtn = `<button class="btn btn-sm" onclick="selectJob(${j.id})">Select</button>`;
          if (j.state !== 'Terminal') {
            actionBtn += ` <button class="btn btn-sm btn-settle" onclick="selectJob(${j.id}); runDeliberation();">Deliberate & Settle</button>`;
          }

          html += `<tr class="clickable-row">
            <td style="color:var(--cyan); font-weight:700;">#${j.id}</td>
            <td><span class="status-pill status-${j.state}">${j.state}</span></td>
            <td>${j.amount_eth} ETH</td>
            <td>${shortClient}</td>
            <td>${shortWorker}</td>
            <td>${split}</td>
            <td>${actionBtn}</td>
          </tr>`;
        });
        tbody.innerHTML = html;
      } catch (e) {
        tbody.innerHTML = '<tr><td colspan="7" style="color:var(--red); text-align:center;">Failed to connect to Base Sepolia node.</td></tr>';
      }
    }

    loadEscrows();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.post("/api/deliberate")
async def deliberate(request: Request):
    payload = await request.json()
    spec = payload.get("task_spec", "")
    evidence = payload.get("evidence", "")

    client = AgentCourtClient()
    precedents = find_relevant_precedents(spec, evidence, top_k=2)
    ruling = client.evaluate(spec, evidence)
    ruling["precedents"] = precedents
    return ruling

@app.post("/api/settle")
async def settle(request: Request):
    if not DEPLOYER_KEY:
        return JSONResponse({"status": "error", "error": "No DEPLOYER_PRIVATE_KEY found in .env"})

    payload = await request.json()
    job_id = payload.get("job_id")
    bps = payload.get("basis_points")

    try:
        account = w3.eth.account.from_key(DEPLOYER_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build resolve transaction
        tx = contract.functions.resolveJob(job_id, bps).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 300000,
            'maxFeePerGas': w3.to_wei('1.5', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('0.1', 'gwei'),
            'chainId': 84532  # Base Sepolia
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=DEPLOYER_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        return JSONResponse({"status": "success", "tx_hash": tx_hash.hex()})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

@app.get("/api/jobs")
def get_jobs():
    try:
        total_jobs = contract.functions.jobCount().call()
    except Exception as e:
        print(f"[!] Error calling jobCount: {e}")
        return []

    jobs_list = []
    selector = w3.keccak(text="jobs(uint256)")[:4]

    for i in range(total_jobs, 0, -1):
        try:
            call_data = selector + i.to_bytes(32, byteorder='big')
            raw_result = w3.eth.call({'to': checksum_address, 'data': call_data})

            chunks = [raw_result[offset:offset+32] for offset in range(0, len(raw_result), 32)]
            
            job_id = int.from_bytes(chunks[0], 'big')
            client_addr = Web3.to_checksum_address(chunks[1][-20:])
            worker_addr = Web3.to_checksum_address(chunks[2][-20:])
            evaluator_addr = Web3.to_checksum_address(chunks[3][-20:])
            amount_wei = int.from_bytes(chunks[4], 'big')
            state_val = int.from_bytes(chunks[8], 'big')
            worker_bps = int.from_bytes(chunks[9], 'big')

            jobs_list.append({
                "id": job_id,
                "client": client_addr,
                "worker": worker_addr,
                "evaluator": evaluator_addr,
                "amount_eth": str(w3.from_wei(amount_wei, "ether")),
                "state": STATE_MAP.get(state_val, "Unknown"),
                "worker_basis_points": worker_bps
            })
        except Exception as e:
            print(f"[!] Error reading job #{i}: {e}")
            continue

    return jobs_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
