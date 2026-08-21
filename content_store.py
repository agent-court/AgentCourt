import json
import os
from web3 import Web3

STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deliverables_store.json")

def _normalize_key(k) -> str:
    if hasattr(k, "hex"):
        k = k.hex()
    k_str = str(k).strip().lower()
    if k_str.startswith("0x"):
        k_str = k_str[2:]
    return k_str.zfill(64)

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
    data = _load_store()
    raw_hash = Web3.keccak(text=spec_text)
    key = _normalize_key(raw_hash)
    data["specs"][key] = spec_text
    _save_store(data)
    return "0x" + key

def register_deliverable(deliv_text: str) -> str:
    data = _load_store()
    raw_hash = Web3.keccak(text=deliv_text)
    key = _normalize_key(raw_hash)
    data["deliverables"][key] = deliv_text
    _save_store(data)
    return "0x" + key

def get_spec_by_hash(spec_hash) -> str:
    if not spec_hash:
        return None
    data = _load_store()
    return data["specs"].get(_normalize_key(spec_hash))

def get_deliverable_by_hash(deliv_hash) -> str:
    if not deliv_hash:
        return None
    data = _load_store()
    return data["deliverables"].get(_normalize_key(deliv_hash))
