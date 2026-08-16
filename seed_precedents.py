import precedent_db

benchmarks = [
    {
        "task_id": 101,
        "spec": "Build a Python script to fetch the last 100 blocks from Base and calculate average gas used in Gwei. Return results in clean JSON format.",
        "deliverable": "def get_gas(): return {'avg_gas_gwei': 0.005, 'blocks_scanned': 100}",
        "opinion": "Worker delivered functional logic matching the mathematical output, but hardcoded mock values instead of actively executing RPC calls. Substantial performance achieved, but missing live integration.",
        "client_share": 60,
        "worker_share": 40
    },
    {
        "task_id": 102,
        "spec": "Write an ERC-20 Solidity contract with an owner-only mint function, 18 decimals, and 1,000,000 initial supply.",
        "deliverable": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport '@openzeppelin/contracts/token/ERC20/ERC20.sol';\nimport '@openzeppelin/contracts/access/Ownable.sol';\ncontract Token is ERC20, Ownable {\n    constructor() ERC20('Test', 'TST') Ownable(msg.sender) {\n        _mint(msg.sender, 1000000 * 10**18);\n    }\n    function mint(address to, uint256 amount) external onlyOwner {\n        _mint(to, amount);\n    }\n}",
        "opinion": "Worker complied 100% with the technical specification, including OpenZeppelin v5 compliance and correct access control.",
        "client_share": 0,
        "worker_share": 100
    },
    {
        "task_id": 103,
        "spec": "Scrape trending crypto tokens on Base and export to CSV with columns: name, symbol, address, 24h_volume.",
        "deliverable": "import requests\n# Placeholder for scraping logic\nprint('Done')",
        "opinion": "Total material breach. Deliverable consists of non-functional placeholder code with zero scraping or data export capabilities.",
        "client_share": 100,
        "worker_share": 0
    },
    {
        "task_id": 104,
        "spec": "Create a FastAPI endpoint /price/{token_address} that returns live price from DexScreener API with 5-second caching.",
        "deliverable": "from fastapi import FastAPI\nimport requests\napp = FastAPI()\n@app.get('/price/{address}')\ndef get_price(address: str):\n    res = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{address}')\n    return res.json()",
        "opinion": "Endpoint functions correctly and pulls live market data from DexScreener, but completely omitted the required 5-second in-memory caching mechanism.",
        "client_share": 25,
        "worker_share": 75
    },
    {
        "task_id": 105,
        "spec": "Develop a TypeScript trading helper function calculating 14-period RSI from an array of closing prices.",
        "deliverable": "function calculateRSI(prices: number[]): number { /* Python syntax error: def calc()... */ }",
        "opinion": "Language mismatch and syntax invalidity. Client explicitly specified TypeScript, while deliverable contained invalid Python fragments that fail compilation.",
        "client_share": 90,
        "worker_share": 10
    }
]

print("⚖️ Seeding AgentCourt ChromaDB Precedent Database...")
for b in benchmarks:
    precedent_db.store_precedent(
        task_id=b["task_id"],
        spec=b["spec"],
        deliverable=b["deliverable"],
        opinion=b["opinion"],
        client_share=b["client_share"],
        worker_share=b["worker_share"]
    )
    print(f"  ✅ Indexed Precedent Case #{b['task_id']}")

print(f"\n🎉 Successfully seeded precedent case law! Total indexed cases: {len(precedent_db.get_all_precedents())}")
