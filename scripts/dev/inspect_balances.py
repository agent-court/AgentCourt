from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

deployer = "0x7807d927C720bdEE226AbaC41E0793326c5b62c6"
treasury = "0xc2eC09e66052927D28574DF4AdF0095fe3C425B6"
worker   = "0x1111111111111111111111111111111111111111"
with open("mainnet_escrow_address.txt") as f:
    escrow = f.read().strip()

USDC_ADDR = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
erc20_abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
usdc = w3.eth.contract(address=w3.to_checksum_address(USDC_ADDR), abi=erc20_abi)

print("==================================================")
print("💰 CURRENT USDC BALANCES ON BASE MAINNET")
print(f"Deployer (Client) : ${usdc.functions.balanceOf(w3.to_checksum_address(deployer)).call() / 1e6:.4f} USDC")
print(f"Worker (0x1111)   : ${usdc.functions.balanceOf(w3.to_checksum_address(worker)).call() / 1e6:.4f} USDC")
print(f"Treasury (1.5%)   : ${usdc.functions.balanceOf(w3.to_checksum_address(treasury)).call() / 1e6:.4f} USDC")
print(f"Escrow Contract   : ${usdc.functions.balanceOf(w3.to_checksum_address(escrow)).call() / 1e6:.4f} USDC")
print("==================================================")
