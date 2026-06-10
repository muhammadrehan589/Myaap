"""RAG Service — Semantic capability matching using ChromaDB + sentence-transformers.

Uses the Capability Library from the Excel workbook as the sole data source.
Embeddings are built from: Domain + Project Summary + Certification + Client Type.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from services.dataset_service import get_capability_records, get_capability_text

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "vector_db")
COLLECTION_NAME = "capabilities"

_embedding_model = None
_collection = None
_indexed = False


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=DB_PATH)
        # Delete old collection if it exists (stale data from capabilities.json)
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def _build_index():
    """Build ChromaDB index from the Excel Capability Library."""
    global _indexed
    if _indexed:
        return

    collection = _get_collection()
    capabilities = get_capability_records()
    model = _get_embedding_model()

    documents = []
    embeddings = []
    ids = []
    metadatas = []

    for cap in capabilities:
        text = get_capability_text(cap)
        documents.append(text)
        embeddings.append(model.encode(text).tolist())
        ids.append(cap["cap_id"])
        metadatas.append({
            "cap_id": cap["cap_id"],
            "domain": cap.get("domain", ""),
            "certification": cap.get("certification", "N/A"),
            "client_type": cap.get("client_type", ""),
            "contract_value": cap.get("contract_value", ""),
            "year_completed": str(cap.get("year_completed", "")),
        })

    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
    _indexed = True


def retrieve_matches(requirements: list[str], top_k: int = 3) -> list[dict]:
    """Semantic search against capability vector DB for each requirement.

    Returns evidence sourced directly from the Excel workbook.
    """
    _build_index()
    model = _get_embedding_model()
    collection = _get_collection()

    matches = []
    for req in requirements:
        query_embedding = model.encode(req).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
        )

        if results["documents"] and results["documents"][0]:
            best_doc = results["documents"][0][0]
            best_meta = results["metadatas"][0][0]
            best_distance = results["distances"][0][0] if results["distances"] else 1.0
            similarity_score = max(0.0, 1.0 - best_distance)

            # Build evidence from actual dataset fields
            evidence_parts = []
            if best_meta.get("domain"):
                evidence_parts.append(f"Domain: {best_meta['domain']}")
            evidence_parts.append(best_doc)
            if best_meta.get("certification") and best_meta["certification"] != "N/A":
                evidence_parts.append(f"Certification: {best_meta['certification']}")
            if best_meta.get("client_type"):
                evidence_parts.append(f"Client Type: {best_meta['client_type']}")

            matches.append({
                "requirement": req,
                "record_id": best_meta.get("cap_id", ""),
                "evidence": " | ".join(evidence_parts),
                "score": round(similarity_score, 4),
            })
        else:
            matches.append({
                "requirement": req,
                "record_id": "",
                "evidence": "No matching capability found in dataset",
                "score": 0.0,
            })

    return matches
