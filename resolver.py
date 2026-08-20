import os
import json
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger("AgentCourt.Resolver")

# Cache directory for local testing
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".court_metadata_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def save_local_payload(data_hash: str, payload: Dict[str, Any]) -> str:
    """Saves metadata locally mapped to its hex hash for development testing."""
    clean_hash = data_hash.lower().replace("0x", "")
    file_path = os.path.join(CACHE_DIR, f"{clean_hash}.json")
    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info(f"Stored metadata locally for hash: 0x{clean_hash[:8]}...")
    return file_path


async def resolve_payload(data_hash_or_uri: str) -> Dict[str, Any]:
    """
    Resolves rich job metadata given a hash or URI.
    Checks:
      1. Local cache
      2. IPFS gateway (if URI starts with ipfs://)
      3. Fallback generic representation
    """
    clean_input = data_hash_or_uri.strip()

    # 1. Check IPFS URI
    if clean_input.startswith("ipfs://"):
        cid = clean_input.replace("ipfs://", "")
        gateway_url = f"https://gateway.pinata.cloud/ipfs/{cid}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(gateway_url)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch IPFS CID {cid}: {e}")

    # 2. Check Local Cache by hash
    clean_hash = clean_input.lower().replace("0x", "")
    file_path = os.path.join(CACHE_DIR, f"{clean_hash}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading cached metadata: {e}")

    # 3. Fallback payload if no metadata found
    return {
        "task_title": "Unresolved Task Metadata",
        "task_specification": "No rich specification found for this hash.",
        "deliverable_content": f"Raw Hash: {data_hash_or_uri}",
        "criteria": "Evaluate based on general standards."
    }

