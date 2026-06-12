"""RAG Service — Optimized semantic capability matching.

Performance optimizations:
1. Cached embedding matrix — loaded once, reused across queries
2. Batch cosine similarity — numpy matrix operations instead of loops
3. Pre-computed embeddings — stored in memory, not re-encoded
4. Optimized top-K — numpy argpartition instead of full sort

Replaces ChromaDB with database-backed vector storage.
Uses pgvector for PostgreSQL or numpy cosine similarity for SQLite.
"""

import os
import json
import logging
import numpy as np
from typing import Optional

from config.database import SessionLocal, IS_POSTGRES
from services.dataset_service import get_capability_records, get_capability_text

logger = logging.getLogger(__name__)

# Cached data — loaded once, reused across all queries
_embedding_model = None
_capability_matrix: Optional[np.ndarray] = None  # (N, 384) embedding matrix
_capability_data: list[dict] = []  # capability metadata
_indexed = False


def _get_embedding_model():
    """Lazy-load the sentence-transformer model (local cache only)."""
    global _embedding_model
    if _embedding_model is None:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        from sentence_transformers import SentenceTransformer

        try:
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


def _build_embedding_matrix(embeddings: list[list[float]]) -> np.ndarray:
    """Convert list of embeddings to numpy matrix for batch operations.

    Args:
        embeddings: List of embedding vectors (each 384-dim)

    Returns:
        numpy array of shape (N, 384)
    """
    return np.array(embeddings, dtype=np.float32)


def _batch_cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between query vector and all rows in matrix.

    Uses vectorized numpy operations for maximum performance.

    Args:
        query: Single embedding vector (384,)
        matrix: Embedding matrix (N, 384)

    Returns:
        Array of similarity scores (N,)
    """
    # Normalize vectors
    query_norm = query / (np.linalg.norm(query) + 1e-8)
    matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8
    matrix_normalized = matrix / matrix_norms

    # Dot product = cosine similarity for normalized vectors
    similarities = np.dot(matrix_normalized, query_norm)

    # Clamp to [0, 1] range
    return np.clip(similarities, 0.0, 1.0)


def _ensure_embeddings():
    """Ensure all capability records have embeddings cached in memory.

    Loads embeddings from database and builds numpy matrix for fast queries.
    """
    global _indexed, _capability_matrix, _capability_data

    if _indexed:
        return

    try:
        from models.capability_library import CapabilityLibrary

        db = SessionLocal()
        try:
            all_caps = db.query(CapabilityLibrary).all()

            if not all_caps:
                logger.warning("No capabilities found in database")
                _indexed = True
                return

            logger.info(f"Loading {len(all_caps)} capabilities into memory...")

            # Check if embeddings exist
            needs_embedding = any(
                cap.embedding is None for cap in all_caps
            )

            if needs_embedding:
                logger.info("Generating missing embeddings...")
                model = _get_embedding_model()
                for cap in all_caps:
                    if cap.embedding is None:
                        text = get_capability_text(cap.to_dict())
                        embedding = model.encode(text).tolist()
                        if IS_POSTGRES:
                            cap.embedding = embedding
                        else:
                            cap.embedding = json.dumps(embedding)
                        cap.embedding_text = text
                db.commit()
                logger.info("Embeddings generated")

            # Build in-memory cache
            embeddings = []
            cap_data = []

            for cap in all_caps:
                embedding = cap.embedding
                if isinstance(embedding, str):
                    embedding = json.loads(embedding)
                if embedding and len(embedding) > 0:
                    embeddings.append(embedding)
                    cap_data.append({
                        "cap_id": cap.cap_id,
                        "domain": cap.domain,
                        "project_summary": cap.project_summary,
                        "certification": cap.certification,
                        "client_type": cap.client_type,
                        "year_completed": cap.year_completed,
                        "contract_value": cap.contract_value,
                        "text": cap.embedding_text or get_capability_text(cap.to_dict()),
                    })

            if embeddings:
                _capability_matrix = _build_embedding_matrix(embeddings)
                _capability_data = cap_data
                logger.info(
                    f"Loaded {len(cap_data)} capabilities with "
                    f"{_capability_matrix.shape[1]}-dim embeddings into memory"
                )
            else:
                logger.warning("No valid embeddings found")

            _indexed = True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        _indexed = True


def retrieve_matches(requirements: list[str], top_k: int = 3) -> list[dict]:
    """Semantic search against capability database for each requirement.

    Uses cached embedding matrix for fast batch similarity computation.

    Args:
        requirements: List of requirement text strings
        top_k: Number of top matches to return per requirement (default: 3)

    Returns:
        List of dicts, one per requirement, with top-k matches.
    """
    _ensure_embeddings()

    if _capability_matrix is None or len(_capability_data) == 0:
        logger.warning("No capabilities available for matching")
        return [{
            "requirement": req,
            "record_id": "",
            "evidence": "No capabilities in database",
            "score": 0.0,
            "top_matches": [],
            "best_score": 0.0,
        } for req in requirements]

    model = _get_embedding_model()

    # Batch encode all requirements at once (faster than one-by-one)
    query_embeddings = model.encode(requirements, batch_size=32).astype(np.float32)

    matches = []
    for req_idx, req in enumerate(requirements):
        query_vec = query_embeddings[req_idx]

        # Batch cosine similarity against ALL capabilities
        similarities = _batch_cosine_similarity(query_vec, _capability_matrix)

        # Get top-K indices using argpartition (O(n) vs O(n log n) for sort)
        k = min(top_k, len(similarities))
        if k > 0:
            top_indices = np.argpartition(similarities, -k)[-k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
        else:
            top_indices = []

        if len(top_indices) > 0:
            # Build top_matches array
            top_matches = []
            for idx in top_indices:
                sim_score = float(similarities[idx])
                cap = _capability_data[idx]
                top_matches.append({
                    "cap_id": cap["cap_id"],
                    "similarity_score": round(sim_score, 4),
                    "domain": cap["domain"],
                    "project_summary": cap["project_summary"],
                    "certification": cap["certification"],
                    "client_type": cap["client_type"],
                    "year_completed": cap["year_completed"],
                })

            best_score = top_matches[0]["similarity_score"]
            best_cap = _capability_data[top_indices[0]]

            # Build evidence string from best match
            evidence_parts = []
            if best_cap["domain"]:
                evidence_parts.append(f"Domain: {best_cap['domain']}")
            evidence_parts.append(best_cap["text"])
            if best_cap["certification"] and best_cap["certification"] != "N/A":
                evidence_parts.append(f"Certification: {best_cap['certification']}")
            if best_cap["client_type"]:
                evidence_parts.append(f"Client Type: {best_cap['client_type']}")

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
