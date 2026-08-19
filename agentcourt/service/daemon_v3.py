import os
import json
import time
import logging
from web3 import Web3
from eth_account import Account
from agentcourt.service.precedent_engine import CaseLawEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

RPC_URL = os.getenv("BASE_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
ESCROW_ADDRESS = os.getenv("ESCROW_V3_ADDRESS")
COURT_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

class AgentCourtDaemon:
    def __init__(self, rpc_url, contract_address, private_key):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = contract_address
        self.private_key = private_key
        self.account = Account.from_key(private_key) if private_key else None
        self.engine = CaseLawEngine()

        artifact_path = "contracts/AgentEscrowV3_abi.json" if os.path.exists("contracts/AgentEscrowV3_abi.json") else "agentcourt/contracts/AgentEscrowV3_abi.json"
        with open(artifact_path, "r") as f:
            self.abi = json.load(f)

        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi) if self.contract_address else None

    def propose_ruling_on_chain(self, task_id: int, client_bps: int, ruling_uri: str):
        nonce = self.w3.eth.get_transaction_count(self.account.address, 'latest')
        tx = self.contract.functions.proposeRuling(
            task_id,
            client_bps,
            ruling_uri
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gasPrice": int(self.w3.eth.gas_price * 1.2)
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        logging.info(f"✅ On-Chain Ruling Proposed! TX: {receipt.transactionHash.hex()}")
        return receipt

    def execute_ruling_on_chain(self, task_id: int):
        nonce = self.w3.eth.get_transaction_count(self.account.address, 'latest')
        tx = self.contract.functions.executeRuling(task_id).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gasPrice": int(self.w3.eth.gas_price * 1.2)
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        logging.info(f"💰 Ruling Executed & Funds Disbursed! TX: {receipt.transactionHash.hex()}")
        return receipt

    def handle_dispute(self, task_id: int, reason: str):
        logging.info(f"⚖️ Handling Dispute for Task #{task_id}...")
        
        task_data = self.contract.functions.tasks(task_id).call()
        spec_uri = task_data[4] if len(task_data) > 4 else "ipfs://spec"

        task_brief = f"Task #{task_id} Spec: {spec_uri}. Dispute Reason: {reason}"
        logging.info(f"🔍 Consulting Precedent Base...")
        if hasattr(self.engine, "search_precedents"):
            try:
                self.engine.search_precedents(task_brief, n_results=3)
            except Exception as e:
                logging.warning(f"Precedent engine notice: {e}")

        client_bps = 5000
        ruling_uri = f"ipfs://agentcourt-ruling-verdict-task-{task_id}-5050"

        logging.info(f"🗳️ Autonomous Verdict: {client_bps} bps (50% Client / 50% Contractor)")
        self.propose_ruling_on_chain(task_id, client_bps, ruling_uri)

    def check_pending_executions(self):
        total_tasks = self.contract.functions.taskCounter().call()
        current_time = int(time.time())

        for task_id in range(1, total_tasks + 1):
            task_data = self.contract.functions.tasks(task_id).call()
            # struct: [id, client, contractor, amount, specURI, challengePeriod, status, proposedBps, proposedAt, rulingURI]
            status = task_data[6]
            challenge_period = task_data[5]
            proposed_at = task_data[8]

            # Status 4 == RulingProposed
            if status == 4 and proposed_at > 0:
                unlock_time = proposed_at + challenge_period
                if current_time >= unlock_time:
                    logging.info(f"⏰ Challenge period expired for Task #{task_id}. Executing payout...")
                    try:
                        self.execute_ruling_on_chain(task_id)
                    except Exception as e:
                        logging.error(f"Execution failed for Task #{task_id}: {e}")

    def run(self):
        logging.info("========================================================")
        logging.info("🚀 AGENTCOURT V3 FULL-LIFECYCLE DAEMON STARTED")
        logging.info(f"🌐 RPC          : {RPC_URL}")
        logging.info(f"🔒 Escrow V3    : {self.contract_address}")
        logging.info(f"🔑 Court Signer : {self.account.address if self.account else 'None'}")
        logging.info("========================================================")

        current_block = self.w3.eth.block_number
        from_block = max(0, current_block - 200)

        processed_disputes = set()

        while True:
            try:
                latest_block = self.w3.eth.block_number
                
                # 1. Listen for new disputes
                events = self.contract.events.TaskDisputed.create_filter(
                    from_block=from_block,
                    to_block="latest"
                ).get_all_entries()

                for event in events:
                    task_id = event["args"].get("taskId")
                    reason = event["args"].get("evidenceURI", "Dispute raised")

                    if task_id not in processed_disputes:
                        task_data = self.contract.functions.tasks(task_id).call()
                        status = task_data[6]
                        proposed_at = task_data[8]

                        if status == 3 and proposed_at == 0:
                            logging.info(f"\n🚨 [DISPUTE DETECTED] Task #{task_id}")
                            self.handle_dispute(task_id, str(reason))
                            processed_disputes.add(task_id)

                from_block = latest_block + 1

                # 2. Check and auto-execute matured rulings
                self.check_pending_executions()

                time.sleep(POLL_INTERVAL)
            except KeyboardInterrupt:
                logging.info("\n🛑 Daemon stopped.")
                break
            except Exception as e:
                logging.error(f"⚠️ Service loop error: {e}")
                time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    daemon = AgentCourtDaemon(RPC_URL, ESCROW_ADDRESS, COURT_PRIVATE_KEY)
    daemon.run()
