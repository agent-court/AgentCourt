import os
from typing import List, Dict, Any
import chromadb

CHROMA_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentcourt_db")

_client = None
_collection = None

def get_precedent_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
        _collection = _client.get_or_create_collection(
            name="agentcourt_precedents",
            metadata={"description": "Historical dispute resolutions for stare decisis deliberation"}
        )
    return _collection

def record_new_precedent(case_id: str, title: str, task_spec: str, fact_summary: str, ruling_basis_points: int):
    collection = get_precedent_collection()
    document_text = f"Title: {title}\nTask: {task_spec}\nFacts: {fact_summary}\nRuling BPS: {ruling_basis_points}"
    collection.add(
        ids=[str(case_id)],
        documents=[document_text],
        metadatas=[{
            "case_id": str(case_id),
            "title": title,
            "ruling_basis_points": int(ruling_basis_points),
            "fact_summary": fact_summary
        }]
    )

def find_relevant_precedents(task_spec: str, deliverable_evidence: str, top_k: int = 2) -> List[Dict[str, Any]]:
    collection = get_precedent_collection()
    query_text = f"Task: {task_spec}\nDeliverable Evidence: {deliverable_evidence}"
    
    count = collection.count()
    if count == 0:
        return []
    
    results = collection.query(
        query_texts=[query_text],
        n_results=min(top_k, count)
    )
    
    precedents = []
    if results and results.get("metadatas") and len(results["metadatas"]) > 0:
        for meta in results["metadatas"][0]:
            precedents.append(meta)
            
    return precedents


def format_precedents_for_prompt(precedents: List[Dict[str, Any]]) -> str:
    if not precedents:
        return "No prior case precedents found. Rely strictly on standard evaluation."
    
    formatted = "### LEGAL PRECEDENTS & PRIOR COURT RULINGS (STARE DECISIS):\n"
    for idx, p in enumerate(precedents, 1):
        formatted += (
            f"Precedent Case #{idx} (Case ID: {p.get("case_id")}):\n"
            f"  - Title / Spec: {p.get("title", "N/A")}\n"
            f"  - Prior Ruling Award: {p.get("ruling_basis_points")} bps\n"
            f"  - Case Facts / Rationale: {p.get("fact_summary", "N/A")}\n\n"
        )
    formatted += "Consider these precedents to maintain consistent judicial standards.\n"
    return formatted
