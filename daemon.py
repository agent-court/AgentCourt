# -*- coding: utf-8 -*-
import time
import logging
from dotenv import load_dotenv
import agent_mainnet as agent
import arbitrator
import precedent_db

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

POLL_INTERVAL_SECONDS = 15

def run_listener_cycle():
    try:
        task_count = agent.escrow_contract.functions.taskCount().call()
        logging.info(f"Scanning Base Mainnet Escrow ({agent.ESCROW_ADDRESS}). Total tasks: {task_count}")

        for task_id in range(1, task_count + 1):
            t = agent.escrow_contract.functions.tasks(task_id).call()
            
            # Access tuple by index to prevent any unpack count errors
            task_id_val = t[0]
            client = t[1]
            worker = t[2]
            amount = t[3]
            spec = t[4]
            deliverable = t[5]
            status = t[6]  # Solidity Enum: 0 = Created, 1 = Submitted, 2 = Resolved

            if status == 1:
                logging.info(f"⚖️ [DISPUTE/SUBMISSION DETECTED] Task #{task_id_val}")
                logging.info(f"   Spec       : {spec[:60]}...")
                logging.info(f"   Deliverable: {deliverable[:60]}...")
                logging.info("Convening 3-Juror AI Panel (Claude Opus, GPT-4o Mini, Gemini Flash)...")

                ruling = arbitrator.arbitrate_task(spec, deliverable)
                logging.info(f"✅ [RULING] Provider: {ruling.get('provider')}")
                logging.info(f"   Split: {ruling.get('client_share_pct')}% Client / {ruling.get('worker_share_pct')}% Worker")
                logging.info(f"   Spec: {ruling.get('spec_adherence')}/100 | Quality: {ruling.get('code_quality')}/100")

                logging.info(f"Executing on-chain settlement for Task #{task_id_val} on Base Mainnet...")
                tx_hash = agent.resolve_task(
                    task_id=task_id_val,
                    client_share_pct=ruling["client_share_pct"],
                    worker_share_pct=ruling["worker_share_pct"],
                    court_opinion=ruling["court_opinion"]
                )

                if tx_hash:
                    logging.info(f"🎉 [SETTLED] Task #{task_id_val} on-chain! Tx: https://basescan.org/tx/{tx_hash}")
                    precedent_db.store_precedent(
                        task_id=task_id_val,
                        spec=spec,
                        deliverable=deliverable,
                        client_share_pct=ruling["client_share_pct"],
                        worker_share_pct=ruling["worker_share_pct"],
                        opinion=ruling["court_opinion"]
                    )
                else:
                    logging.error(f"❌ [ERROR] Failed settlement transaction on Task #{task_id_val}.")

    except Exception as e:
        logging.error(f"Error during daemon cycle: {e}")

def main():
    logging.info("========================================================")
    logging.info("🚀 AGENTCOURT 24/7 AUTONOMOUS LISTENER DAEMON STARTED")
    logging.info(f"🌐 Target Network : Base Mainnet (Chain ID 8453)")
    logging.info(f"🔒 Escrow Address : {agent.ESCROW_ADDRESS}")
    logging.info(f"⏱️  Polling Rate   : Every {POLL_INTERVAL_SECONDS}s")
    logging.info("========================================================")

    while True:
        run_listener_cycle()
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
