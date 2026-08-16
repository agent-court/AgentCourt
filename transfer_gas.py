import time
from agent import w3, CLIENT_ADDR, WORKER_ADDR, PRIVATE_KEY, get_raw_tx

print(f"Transferring 0.002 ETH from Client ({CLIENT_ADDR}) to Worker ({WORKER_ADDR})...")
nonce = w3.eth.get_transaction_count(CLIENT_ADDR, "pending")
gas_price = int(w3.eth.gas_price * 1.5)

tx = {
    "to": WORKER_ADDR,
    "value": w3.to_wei(0.002, "ether"),
    "gas": 21000,
    "gasPrice": gas_price,
    "nonce": nonce,
    "chainId": 84532,
}

signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed))
print(f"Broadcasting Tx: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
print(f"Receipt status: {receipt.status} (1 = Success)")

time.sleep(3)
bal = w3.eth.get_balance(WORKER_ADDR)
print(f"Confirmed Worker Balance: {w3.from_wei(bal, 'ether')} ETH")
