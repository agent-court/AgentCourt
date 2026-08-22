from agent import w3, CLIENT_ADDR, WORKER_ADDR, PRIVATE_KEY, get_raw_tx, build_tx_params

print("--- Current Balances ---")
c_bal = w3.eth.get_balance(CLIENT_ADDR)
w_bal = w3.eth.get_balance(WORKER_ADDR)
print(f"Client Address: {CLIENT_ADDR}")
print(f"Client Balance: {w3.from_wei(c_bal, 'ether')} ETH")
print(f"Worker Address: {WORKER_ADDR}")
print(f"Worker Balance: {w3.from_wei(w_bal, 'ether')} ETH\n")

print("⛽ Transferring 0.001 ETH to Worker...")
params = build_tx_params(CLIENT_ADDR)
params["to"] = WORKER_ADDR
params["value"] = w3.to_wei("0.001", "ether")
params["gas"] = 21000

signed = w3.eth.account.sign_transaction(params, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed))
print(f"Transfer tx broadcasted: {tx_hash.hex()}")
w3.eth.wait_for_transaction_receipt(tx_hash)

new_w_bal = w3.eth.get_balance(WORKER_ADDR)
print(f"✅ Updated Worker Balance: {w3.from_wei(new_w_bal, 'ether')} ETH")
