import logging
from web3 import Web3

logger = logging.getLogger("AgentCourt.RPC")

BASE_SEPOLIA_RPCS = [
    "https://base-sepolia-rpc.publicnode.com",
    "https://sepolia.base.org",
    "https://1rpc.io/base-sepolia",
    "https://base-sepolia.blockpi.network/v1/rpc/public"
]

def get_resilient_w3(timeout: int = 12) -> Web3:
    """Iterates through RPC endpoints and returns a healthy Web3 instance."""
    for rpc in BASE_SEPOLIA_RPCS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": timeout}))
            if w3.is_connected():
                logger.info(f"Connected to Base Sepolia via {rpc}")
                return w3
        except Exception as e:
            logger.warning(f"RPC endpoint {rpc} failed: {e}. Trying next...")
            continue
    raise ConnectionError("All Base Sepolia RPC providers are currently unreachable.")
