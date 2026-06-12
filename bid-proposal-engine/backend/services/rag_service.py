"""RAG Service — Semantic capability matching using database + sentence-transformers.

Replaces ChromaDB with database-backed vector storage.
Uses pgvector for PostgreSQL or numpy cosine similarity for SQLite.
"""

import os
import json
import logging
import numpy as np

from config.database import SessionLocal, IS_POSTGRES
from services.dataset_service import get_capability_records, get_capability_text

logger = logging.getLogger(__name__)

_embedding_model = None
_indexed = False


def _get_embedding_model():
    """Lazy-load the sentence-transformer model (local cache only)."""
    global _embedding_model
    if _embedding_model is None:
        import os
        # Ensure offline mode is set before loading
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        # Import here to avoid module-level import issues
        from sentence_transformers import SentenceTransformer

        try:
            # Try loading with local_files_only first (fastest)
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            logger.info("Loaded embedding model from local cache")
        except Exception as e:
            logger.warning(f"Local cache load failed: {e}, trying with network...")
            try:
                _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded embedding model from network")
            except Exception as e2:
                logger.error(f"Failed to load embedding model: {e2}")
                raise RuntimeError(f"Cannot load embedding model: {e2}")
    return _embedding_model


def _cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    dot = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def _ensure_embeddings():
    """Ensure all capability records have embeddings in the database.

    Always regenerates embeddings to ensure they match the current
    capability text format (natural language, not metadata).
    """
    global _indexed
    if _indexed:
        return

    try:
        from models.capability_library import CapabilityLibrary

        db = SessionLocal()
        try:
            # Always regenerate all embeddings to ensure consistency
            # This ensures embeddings match the current text format
            all_caps = db.query(CapabilityLibrary).all()

            if not all_caps:
                logger.warning("No capabilities found in database")
                _indexed = True
                return

            logger.info(f"Generating embeddings for {len(all_caps)} capabilities...")
            model = _get_embedding_model()

            for cap in all_caps:
                text = get_capability_text(cap.to_dict())
                embedding = model.encode(text).tolist()

                if IS_POSTGRES:
                    cap.embedding = embedding
                else:
                    cap.embedding = json.dumps(embedding)
                cap.embedding_text = text

            db.commit()
            logger.info(f"Generated embeddings for {len(all_caps)} capabilities")

            _indexed = True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        _indexed = True


def retrieve_matches(requirements: list[str], top_k: int = 3) -> list[dict]:
    """Semantic search against capability database for each requirement.

    Returns TOP-K matches per requirement with full capability details.
    Each match includes: cap_id, similarity_score, domain, evidence.

    Args:
        requirements: List of requirement text strings
        top_k: Number of top matches to return per requirement (default: 3)

    Returns:
        List of dicts, one per requirement, each containing:
        - requirement: original text
        - top_matches: list of top-k matches with cap_id, similarity_score, domain, evidence
        - best_score: highest similarity score
        - record_id: cap_id of best match
        - evidence: evidence string of best match
        - score: best_score (for backward compatibility)
    """
    _ensure_embeddings()

    model = _get_embedding_model()

    try:
        from models.capability_library import CapabilityLibrary

        db = SessionLocal()
        try:
            caps = db.query(CapabilityLibrary).all()

            if not caps:
                logger.warning("No capabilities found in database")
                return [{
                    "requirement": req,
                    "record_id": "",
                    "evidence": "No capabilities in database",
                    "score": 0.0,
                    "top_matches": [],
                    "best_score": 0.0,
                } for req in requirements]

            # Build embedding matrix
            cap_data = []
            for cap in caps:
                embedding = cap.embedding
                if isinstance(embedding, str):
                    embedding = json.loads(embedding)
                if embedding:
                    cap_data.append({
                        "cap_id": cap.cap_id,
                        "domain": cap.domain,
                        "project_summary": cap.project_summary,
                        "certification": cap.certification,
                        "client_type": cap.client_type,
                        "year_completed": cap.year_completed,
                        "contract_value": cap.contract_value,
                        "embedding": embedding,
                        "text": cap.embedding_text or get_capability_text(cap.to_dict()),
                    })

            if not cap_data:
                return [{
                    "requirement": req,
                    "record_id": "",
                    "evidence": "No embeddings available",
                    "score": 0.0,
                    "top_matches": [],
                    "best_score": 0.0,
                } for req in requirements]

            # Query for each requirement
            matches = []
            for req_idx, req in enumerate(requirements):
                query_embedding = model.encode(req).tolist()

                # Compute similarities against ALL capabilities
                similarities = []
                for cd in cap_data:
                    sim = _cosine_similarity(query_embedding, cd["embedding"])
                    similarities.append((sim, cd))

                # Sort by similarity descending
                similarities.sort(key=lambda x: x[0], reverse=True)

                # Take top-k results
                top_results = similarities[:min(top_k, len(similarities))]

                if top_results:
                    # Build top_matches array
                    top_matches = []
                    for sim_score, cap in top_results:
                        similarity_score = max(0.0, sim_score)
                        top_matches.append({
                            "cap_id": cap["cap_id"],
                            "similarity_score": round(similarity_score, 4),
                            "domain": cap["domain"],
                            "project_summary": cap["project_summary"],
                            "certification": cap["certification"],
                            "client_type": cap["client_type"],
                            "year_completed": cap["year_completed"],
                        })

                    best_score = top_matches[0]["similarity_score"]
                    best_cap = top_results[0][1]

                    # Build evidence string from best match
                    evidence_parts = []
                    if best_cap["domain"]:
                        evidence_parts.append(f"Domain: {best_cap['domain']}")
                    evidence_parts.append(best_cap["text"])
                    if best_cap["certification"] and best_cap["certification"] != "N/A":
                        evidence_parts.append(f"Certification: {best_cap['certification']}")
                    if best_cap["client_type"]:
                        evidence_parts.append(f"Client Type: {best_cap['client_type']}")

                    # Log retrieval results
                    logger.info(
                        f"RAG [{req_idx+1}/{len(requirements)}]: "
                        f"'{req[:50]}...' → "
                        f"best={best_score:.4f} ({best_cap['cap_id']} {best_cap['domain']}) | "
                        f"top3={[f'{m['cap_id']}({m['similarity_score']:.3f})' for m in top_matches]}"
                    )

                    matches.append({
                        "requirement": req,
                        "record_id": best_cap["cap_id"],
                        "evidence": " | ".join(evidence_parts),
                        "score": best_score,
                        "top_matches": top_matches,
                        "best_score": best_score,
                    })
                else:
                    logger.warning(f"RAG [{req_idx+1}/{len(requirements)}]: '{req[:50]}...' → NO MATCHES")
                    matches.append({
                        "requirement": req,
                        "record_id": "",
                        "evidence": "No matching capability found in dataset",
                        "score": 0.0,
                        "top_matches": [],
                        "best_score": 0.0,
                    })

            return matches
        finally:
            db.close()
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return [{
            "requirement": req,
            "record_id": "",
            "evidence": f"Retrieval error: {e}",
            "score": 0.0,
            "top_matches": [],
            "best_score": 0.0,
        } for req in requirements]
