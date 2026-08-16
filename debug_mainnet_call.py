import json
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

with open("mainnet_escrow_address.txt") as f:
    escrow_addr = w3.to_checksum_address(f.read().strip())

with open("treasury_address.txt") as f:
    treasury_addr = w3.to_checksum_address(f.read().strip())

usdc_addr = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

print(f"Connected to Base: {w3.is_connected()}")
print(f"Escrow Address   : {escrow_addr}")
print(f"Treasury Address : {treasury_addr}")

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)

escrow = w3.eth.contract(address=escrow_addr, abi=escrow_abi)

try:
    tc = escrow.functions.taskCount().call()
    print(f"✅ Escrow taskCount() success: {tc}")
except Exception as e:
    print(f"❌ Escrow taskCount() failed: {e}")

standard_erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]
usdc = w3.eth.contract(address=usdc_addr, abi=standard_erc20_abi)

try:
    treasury_bal = usdc.functions.balanceOf(treasury_addr).call()
    print(f"✅ Treasury USDC balanceOf: {treasury_bal / 1e6} USDC")
except Exception as e:
    print(f"❌ Treasury balanceOf failed: {e}")

try:
    escrow_bal = usdc.functions.balanceOf(escrow_addr).call()
    print(f"✅ Escrow USDC balanceOf: {escrow_bal / 1e6} USDC")
except Exception as e:
    print(f"❌ Escrow balanceOf failed: {e}")
