import json
import os
import chromadb
from chromadb.utils import embedding_functions

class CaseLawEngine:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Use Chroma's native default embedding function
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="agent_case_law",
            embedding_function=self.embedding_fn
        )

    def record_ruling(self, task_id: int, spec_text: str, dispute_reason: str, evidence_summary: str, contractor_bps: int, jury_rationale: str):
        """Index a settled case into the vector database."""
        document_text = f"Task Spec: {spec_text}\nDispute: {dispute_reason}\nEvidence: {evidence_summary}"
        
        metadata = {
            "task_id": int(task_id),
            "contractor_bps": int(contractor_bps),
            "contractor_percent": f"{contractor_bps / 100:.1f}%",
            "jury_rationale": jury_rationale[:1000]
        }

        self.collection.upsert(
            documents=[document_text],
            metadatas=[metadata],
            ids=[f"case_{task_id}"]
        )
        print(f"✅ Precedent indexed for Task #{task_id} ({metadata['contractor_percent']} split)")

    def find_precedents(self, current_spec: str, current_dispute: str, n_results: int = 3):
        """Retrieve the most semantically relevant past rulings using vector search."""
        query_text = f"Task Spec: {current_spec}\nDispute: {current_dispute}"
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        precedents = []
        if results and results["metadatas"] and len(results["metadatas"][0]) > 0:
            for i, meta in enumerate(results["metadatas"][0]):
                precedents.append({
                    "task_id": meta["task_id"],
                    "contractor_percent": meta["contractor_percent"],
                    "jury_rationale": meta["jury_rationale"],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        return precedents

if __name__ == "__main__":
    engine = CaseLawEngine()
    
    # Add a mock precedent
    engine.record_ruling(
        task_id=101,
        spec_text="Write a Python scraper for SEC Edgar filings with rate limiting",
        dispute_reason="Scraper works but crashes on XML filings without error handling",
        evidence_summary="Unit tests fail on 2/10 edge cases. 80% coverage delivered.",
        contractor_bps=7500,
        jury_rationale="Core scraping functionality was delivered and adheres to rate limiting, but XML parsing had partial regressions. 75% payout awarded."
    )

    # Search for similar cases via embeddings
    matches = engine.find_precedents(
        current_spec="Scrape company filings with retry logic",
        current_dispute="Missed several nested tables in filings"
    )
    print("\n🔍 Vector Search Match Result:")
    print(json.dumps(matches, indent=2))
