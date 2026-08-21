"""
AgentCourt Multi-Wallet Protocol Configuration
"""

CONTRACT_ADDRESS = "0x00A0197635788C997AE443C0281E86FB495CD08b"

WALLETS = {
    "treasury": {
        "address": "0x6F8beD09195f041902e1a1640569FDa8cBeb3E3c",
        "role": "Deployer / Oracle / Deliberation Engine"
    },
    "client": {
        "address": "0x45a9fB1b632F12Cdb0Bc0925d189C19Df7CAB1ab",
        "role": "Task Creator & Escrow Depositor"
    },
    "worker": {
        "address": "0x0270FE1033b0460D7f3d2C1333D6EBf1B6d1eB77",
        "role": "Service Provider & Deliverable Submitter"
    }
}
