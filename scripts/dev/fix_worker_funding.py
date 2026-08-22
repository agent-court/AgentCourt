import time
from agent import w3, CLIENT_ADDR, PRIVATE_KEY, WORKER_KEY, get_raw_tx

worker_acct = w3.eth.account.from_key(WORKER_KEY)
worker_addr = worker_acct.address

print(f"Client Address : {CLIENT_ADDR}")
print(f"Worker Address : {worker_addr}")

nonce = w3.eth.get_transaction_count(CLIENT_ADDR, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
max_priority_fee = w3.to_wei("0.1", "gwei")
max_fee = base_fee * 2 + max_priority_fee

# Use 50,000 gas limit to accommodate L2 execution + rollup overhead
tx = {
    "from": CLIENT_ADDR,
    "to": worker_addr,
    "value": w3.to_wei("0.002", "ether"),
    "nonce": nonce,
    "gas": 50000,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": max_priority_fee,
    "chainId": 84532,
    "type": 2,
}

signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed))
print(f"Broadcasted Tx: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"Status : {'SUCCESS (1)' if receipt.status == 1 else 'FAILED (0)'} in block {receipt.blockNumber}")

time.sleep(2)
updated_bal = w3.eth.get_balance(worker_addr)
print(f"✅ Confirmed Worker Balance: {w3.from_wei(updated_bal, 'ether')} ETH")
