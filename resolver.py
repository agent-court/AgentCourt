import os
import json
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AgentCourt.Resolver")

# Local cache directory fallback
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".court_metadata_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

PINATA_JWT = os.getenv("PINATA_JWT")
PINATA_GATEWAY = os.getenv("PINATA_GATEWAY", "gateway.pinata.cloud")


async def pin_json_to_ipfs(payload: Dict[str, Any], name: Optional[str] = None) -> Optional[str]:
    """
    Pins a JSON payload to IPFS using Pinata API.
    Returns: 'ipfs://<CID>' or None on failure.
    """
    if not PINATA_JWT or PINATA_JWT == "your_pinata_jwt_token_here":
        logger.warning("PINATA_JWT not configured. Falling back to local cache.")
        return None

    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Authorization": f"Bearer {PINATA_JWT}",
        "Content-Type": "application/json"
    }
    body = {
        "pinataContent": payload,
        "pinataMetadata": {
            "name": name or "AgentCourt_Metadata"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code == 200:
                cid = resp.json().get("IpfsHash")
                logger.info(f"Successfully pinned to IPFS: ipfs://{cid}")
                return f"ipfs://{cid}"
            else:
                logger.error(f"Pinata pinning failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.error(f"Pinata IPFS request exception: {e}")

    return None


def save_local_payload(data_hash: str, payload: Dict[str, Any]) -> str:
    """Saves metadata locally mapped to its hex hash for development fallback."""
    clean_hash = data_hash.lower().replace("0x", "")
    file_path = os.path.join(CACHE_DIR, f"{clean_hash}.json")
    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info(f"Stored metadata locally for hash: 0x{clean_hash[:8]}...")
    return file_path


async def resolve_payload(data_hash_or_uri: str) -> Dict[str, Any]:
    """
    Resolves rich job metadata given an ipfs:// CID, gateway URL, or raw hash.
    """
    clean_input = data_hash_or_uri.strip()

    # 1. Handle IPFS URI or direct CID
    if clean_input.startswith("ipfs://") or clean_input.startswith("Qm") or clean_input.startswith("bafy"):
        cid = clean_input.replace("ipfs://", "")
        gateway_url = f"https://{PINATA_GATEWAY}/ipfs/{cid}"
        try:
            headers = {}
            if PINATA_JWT and "pinata.cloud" in PINATA_GATEWAY:
                headers["Authorization"] = f"Bearer {PINATA_JWT}"

            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get(gateway_url, headers=headers)
                if resp.status_code == 200:
                    logger.info(f"Resolved metadata from IPFS: {cid[:12]}...")
                    return resp.json()
                else:
                    logger.warning(f"IPFS Gateway returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Failed to fetch IPFS CID {cid}: {e}")

    # 2. Handle Local Cache Fallback
    clean_hash = clean_input.lower().replace("0x", "")
    file_path = os.path.join(CACHE_DIR, f"{clean_hash}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                logger.info(f"Resolved metadata from local cache for 0x{clean_hash[:8]}...")
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading cached metadata: {e}")

    # 3. Fallback generic representation
    return {
        "task_title": "Unresolved Task Metadata",
        "task_specification": "No rich specification found for this hash.",
        "deliverable_content": f"Raw Hash: {data_hash_or_uri}",
        "criteria": "Evaluate based on general standards."
    }
