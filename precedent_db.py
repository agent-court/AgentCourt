import json
import os
import time

DB_FILE = "precedents.json"

def _load_db() -> list:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_db(data: list):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def store_precedent(
    task_id: int,
    spec: str,
    deliverable: str,
    client_share: int,
    worker_share: int,
    opinion: str,
    category: str = "general"
):
    records = _load_db()
    
    # Avoid duplicate task_id entries
    records = [r for r in records if r.get("task_id") != task_id]
    
    entry = {
        "task_id": task_id,
        "spec": spec,
        "deliverable": deliverable,
        "client_share_pct": client_share,
        "worker_share_pct": worker_share,
        "opinion": opinion,
        "category": category,
        "timestamp": int(time.time())
    }
    records.append(entry)
    _save_db(records)
    return entry

def query_relevant_precedents(spec: str, deliverable: str, n_results: int = 2) -> list:
    records = _load_db()
    if not records:
        return []

    # Semantic keyword overlap scoring
    query_tokens = set(f"{spec} {deliverable}".lower().split())
    scored = []

    for r in records:
        doc_tokens = set(f"{r.get('spec', '')} {r.get('deliverable', '')}".lower().split())
        if not doc_tokens:
            continue
        overlap = len(query_tokens.intersection(doc_tokens))
        union = len(query_tokens.union(doc_tokens))
        similarity = overlap / union if union > 0 else 0.0
        scored.append((similarity, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, r in scored[:n_results]:
        item = dict(r)
        item["similarity"] = round(sim, 3)
        results.append(item)
    return results

def get_all_precedents() -> list:
    return _load_db()
