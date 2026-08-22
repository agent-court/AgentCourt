import json
import time
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
account = w3.eth.account.from_key(config["PRIVATE_KEY"])
deployer = account.address

with open("mainnet_escrow_address.txt") as f:
    escrow_addr = w3.to_checksum_address(f.read().strip())

with open("escrow_abi.json") as f:
    escrow_abi = json.load(f)

erc20_abi = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"}
]

USDC_ADDRESS = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
escrow = w3.eth.contract(address=escrow_addr, abi=escrow_abi)
usdc = w3.eth.contract(address=USDC_ADDRESS, abi=erc20_abi)

print(f"Deployer : {deployer}")
print(f"Escrow   : {escrow_addr}")
print(f"Balance  : {usdc.functions.balanceOf(deployer).call() / 1e6} USDC")
print(f"Allowance: {usdc.functions.allowance(deployer, escrow_addr).call() / 1e6} USDC")

# Check contract variables
try:
    print(f"Contract token : {escrow.functions.usdcToken().call()}")
except Exception as e:
    print(f"Could not read usdcToken: {e}")

try:
    print(f"Contract court : {escrow.functions.court().call()}")
except Exception as e:
    print(f"Could not read court: {e}")

# Simulate createTask via eth_call
worker = w3.to_checksum_address("0x1111111111111111111111111111111111111111")
amount = 1_000_000
spec = "Test spec"
deadline = int(time.time()) + 86400

try:
    escrow.functions.createTask(worker, amount, spec, deadline).call({"from": deployer})
    print("✅ Simulation Success: createTask will succeed!")
except Exception as err:
    print(f"❌ Simulation Failed with Error: {err}")
