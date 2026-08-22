import time, os, json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDRESS", "0xaC0571eDdFC330f1CAAE19803352Ea55B9dFE720")
ARBITRATOR_KEY = os.getenv("ARBITRATOR_PRIVATE_KEY") or os.getenv("CLIENT_PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

ESCROW_ABI = [
    {"inputs": [], "name": "taskCount", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
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
            {"internalType": "uint256", "name": "_taskId", "type": "uint256"},
            {"internalType": "uint8", "name": "_verdict", "type": "uint8"}
        ],
        "name": "resolveTask",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDR), abi=ESCROW_ABI)

def monitor_escrow_events(poll_interval=15):
    print("⚖️  AgentCourt Autonomous Arbitration Daemon Starting...")
    print(f"📡 Connected to Base (Chain ID {w3.eth.chain_id})")
    print(f"📄 Watching Contract: {CONTRACT_ADDR}")
    
    while True:
        try:
            total_tasks = contract.functions.taskCount().call()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Polling Base Mainnet... Total Tasks: {total_tasks}")
            
            for task_id in range(1, total_tasks + 1):
                task = contract.functions.tasks(task_id).call()
                status = task[6]
                
                # Status Enum: 0=Created, 1=Submitted, 2=Resolved, 3=Disputed
                if status == 1:
                    print(f"🟡 Task #{task_id} has a submitted deliverable. Ready for jury verification.")
                elif status == 2:
                    print(f"🔵 Task #{task_id} is Resolved.")
                elif status == 3:
                    print(f"🔴 Task #{task_id} is in DISPUTE. Triggering multi-agent jury deliberation...")
                    
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n🛑 Daemon stopped by operator.")
            break
        except Exception as e:
            print(f"⚠️ Polling exception: {e}")
            time.sleep(poll_interval)

if __name__ == "__main__":
    monitor_escrow_events()
