import json
import os
from web3 import Web3

STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deliverables_store.json")

def _load_store() -> dict:
    if not os.path.exists(STORE_PATH):
        with open(STORE_PATH, "w") as f:
            json.dump({"specs": {}, "deliverables": {}}, f)
        return {"specs": {}, "deliverables": {}}
    try:
        with open(STORE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"specs": {}, "deliverables": {}}

def _save_store(data: dict):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def register_spec(spec_text: str) -> str:
    """Computes Keccak hash and stores the raw task spec."""
    data = _load_store()
    spec_hash = Web3.keccak(text=spec_text).hex()
    data["specs"][spec_hash.lower()] = spec_text
    _save_store(data)
    return spec_hash

def register_deliverable(deliv_text: str) -> str:
    """Computes Keccak hash and stores the raw deliverable code/text."""
    data = _load_store()
    deliv_hash = Web3.keccak(text=deliv_text).hex()
    data["deliverables"][deliv_hash.lower()] = deliv_text
    _save_store(data)
    return deliv_hash

def get_spec_by_hash(spec_hash: str) -> str:
    data = _load_store()
    return data["specs"].get(spec_hash.lower())

def get_deliverable_by_hash(deliv_hash: str) -> str:
    data = _load_store()
    return data["deliverables"].get(deliv_hash.lower())
