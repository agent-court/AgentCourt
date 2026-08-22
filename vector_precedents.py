"""
AgentCourt - Precedent Case Law Engine ("Machine Stare Decisis")
Provides persistent semantic indexing and deterministic retrieval of historical rulings.
"""

import os
import json
import chromadb
from typing import List, Dict, Any, Optional

CHROMA_PERSIST_DIR = os.getenv("CHROMA_DIR", "chroma_db")


class PrecedentEngine:
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="agentcourt_precedents",
            metadata={"hnsw:space": "cosine"}
        )

    def record_precedent(
        self,
        case_id: str,
        facts: str,
        issue: str,
        worker_bps: int,
        client_bps: int,
        reasoning: str,
        tags: Optional[List[str]] = None,
        verdict_hash: Optional[str] = None
    ) -> None:
        """Indexes a settled case into persistent vector memory."""
        document_text = f"FACTS: {facts}\nISSUE: {issue}\nREASONING: {reasoning}"
        metadata = {
            "case_id": case_id,
            "worker_bps": worker_bps,
            "client_bps": client_bps,
            "tags": json.dumps(tags or []),
            "verdict_hash": verdict_hash or ""
        }

        self.collection.upsert(
            documents=[document_text],
            metadatas=[metadata],
            ids=[case_id]
        )
        print(f"🏛️ Indexed precedent {case_id} (Worker BPS: {worker_bps})")

    def query_precedents(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k relevant case law precedents for juror context."""
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(top_k, count)
        )

        precedents = []
        if results and results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                doc = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                case_data = {
                    "case_id": meta.get("case_id"),
                    "facts_and_issue": doc,
                    "worker_bps": meta.get("worker_bps"),
                    "client_bps": meta.get("client_bps"),
                    "tags": json.loads(meta.get("tags", "[]")),
                    "verdict_hash": meta.get("verdict_hash")
                }
                precedents.append(case_data)
        return precedents
