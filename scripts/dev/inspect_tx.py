import json
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

tx_hash = "0x44904c7cef9908a343b19ee477e2e89601378bafb0b97768f13b49e660da86cd"
receipt = w3.eth.get_transaction_receipt(tx_hash)

print("==================================================")
print("🔍 TRANSACTION TRANSFER EVENT LOGS")
print(f"Status: {'Success (1)' if receipt.status == 1 else 'Reverted'}")
print(f"Total Logs Emitted: {len(receipt.logs)}")
print("==================================================")

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

for i, log in enumerate(receipt.logs):
    if log.topics and log.topics[0].hex() == TRANSFER_TOPIC:
        from_addr = "0x" + log.topics[1].hex()[-40:]
        to_addr = "0x" + log.topics[2].hex()[-40:]
        amount_raw = int(log.data.hex(), 16)
        print(f"Log #{i+1} [USDC Transfer]:")
        print(f"  From  : {from_addr}")
        print(f"  To    : {to_addr}")
        print(f"  Amount: ${amount_raw / 1e6:.4f} USDC ({amount_raw} raw units)\n")

with open("mainnet_escrow_address.txt") as f:
    escrow_addr = w3.to_checksum_address(f.read().strip())

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)

escrow = w3.eth.contract(address=escrow_addr, abi=escrow_abi)
print("Contract Config On-Chain:")
print(f"  Fee Bps : {escrow.functions.feeBps().call()} bps")
print(f"  Treasury: {escrow.functions.treasury().call()}")
