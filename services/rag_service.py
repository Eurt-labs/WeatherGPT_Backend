import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger("weathergpt.rag")

QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "weathergpt_rag").strip()
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIMENSION = 384

_qdrant_client = None
_embedding_model = None

def get_embedding_model():
    """Lazy-load the FastEmbed embedding model (BAAI/bge-small-en-v1.5, 384-dim)."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from fastembed import TextEmbedding
            logger.info(f"Loading FastEmbed model: {EMBEDDING_MODEL_NAME}")
            _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.error(f"Failed to load FastEmbed model: {e}")
            return None
    return _embedding_model

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate a 384-dimensional vector embedding for a given text."""
    model = get_embedding_model()
    if model is None:
        return None
    try:
        embeddings = list(model.embed([text]))
        if embeddings and len(embeddings) > 0:
            return embeddings[0].tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
    return None

def get_qdrant_client():
    """Lazy-load and return the QdrantClient instance."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    if not QDRANT_URL or not QDRANT_API_KEY:
        logger.warning("Qdrant credentials missing. Set QDRANT_URL and QDRANT_API_KEY in .env.")
        return None

    try:
        from qdrant_client import QdrantClient
        # Handle trailing slashes or port specifics in URL
        cleaned_url = QDRANT_URL.rstrip("/")
        _qdrant_client = QdrantClient(
            url=cleaned_url,
            api_key=QDRANT_API_KEY,
            timeout=10.0
        )
        logger.info(f"Connected to Qdrant Cloud at {cleaned_url}")
        return _qdrant_client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return None

def search_rag(
    query: str,
    sector: Optional[str] = None,
    limit: int = 2,
    score_threshold: float = 0.45
) -> List[Dict[str, Any]]:
    """
    Search Qdrant Cloud for the most relevant knowledge base chunks.
    Optionally filter by sector (agriculture, disaster, urban, aviation, meteorology, regional).
    """
    client = get_qdrant_client()
    if client is None:
        return []

    query_vector = generate_embedding(query)
    if query_vector is None:
        return []

    try:
        from qdrant_client.http import models

        # Build sector filter if applicable
        query_filter = None
        if sector and sector.lower() not in ["general", "all", "none"]:
            sec_term = sector.lower()
            if "agri" in sec_term or "farm" in sec_term:
                sec_term = "agriculture"
            elif "disaster" in sec_term or "flood" in sec_term or "cyclone" in sec_term:
                sec_term = "disaster_management"
            elif "urban" in sec_term or "commute" in sec_term or "aqi" in sec_term:
                sec_term = "urban_mobility"
            elif "aviation" in sec_term or "flight" in sec_term or "cargo" in sec_term:
                sec_term = "aviation_cargo"
            elif "metro" in sec_term or "weather" in sec_term:
                sec_term = "meteorology_core"
            elif "region" in sec_term or "state" in sec_term or "india" in sec_term:
                sec_term = "india_regional"

            query_filter = models.Filter(
                should=[
                    models.FieldCondition(
                        key="sector",
                        match=models.MatchValue(value=sec_term)
                    )
                ]
            )

        search_result = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True
        )

        # Fallback to unfiltered search if filtered search gave 0 results
        if not search_result and query_filter:
            search_result = client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )

        results = []
        for point in search_result:
            payload = point.payload or {}
            results.append({
                "id": point.id,
                "score": round(float(point.score), 4),
                "title": payload.get("title", "Advisory Rule"),
                "sector": payload.get("sector", "meteorology"),
                "filename": payload.get("filename", ""),
                "content": payload.get("content", "")
            })
        return results
    except Exception as e:
        logger.warning(f"Qdrant RAG search error: {e}")
        return []

def format_rag_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved RAG chunks into an authoritative prompt section."""
    if not chunks:
        return ""

    formatted_lines = [
        "OFFICIAL DOMAIN KNOWLEDGE & ADVISORY GUIDELINES (Retrieved from IMD / ICAR / NDMA / CWC):"
    ]
    for i, c in enumerate(chunks, 1):
        title = c.get("title", f"Rule {i}")
        sector = c.get("sector", "general").upper()
        content = c.get("content", "").strip()
        formatted_lines.append(f"\n--- [Source {i}: {title} ({sector})] ---\n{content}")

    return "\n".join(formatted_lines)

def get_rag_status() -> Dict[str, Any]:
    """Check connectivity and stats for the Qdrant Cloud collection."""
    has_url = bool(QDRANT_URL)
    has_key = bool(QDRANT_API_KEY)
    
    if not has_url or not has_key:
        return {
            "status": "unconfigured",
            "message": "QDRANT_URL or QDRANT_API_KEY is not set in .env",
            "collection": QDRANT_COLLECTION,
            "connected": False
        }

    client = get_qdrant_client()
    if client is None:
        return {
            "status": "error",
            "message": "Failed to initialize QdrantClient",
            "collection": QDRANT_COLLECTION,
            "connected": False
        }

    try:
        collections_resp = client.get_collections()
        existing_names = [c.name for c in collections_resp.collections]
        if QDRANT_COLLECTION not in existing_names:
            return {
                "status": "collection_missing",
                "message": f"Connected to Qdrant Cloud, but collection '{QDRANT_COLLECTION}' is not created yet. Run `python scripts/ingest_rag.py` to populate it.",
                "connected": True,
                "available_collections": existing_names,
                "points_count": 0
            }

        coll_info = client.get_collection(collection_name=QDRANT_COLLECTION)
        return {
            "status": "ready",
            "message": f"Connected to Qdrant Cloud collection '{QDRANT_COLLECTION}'",
            "connected": True,
            "collection": QDRANT_COLLECTION,
            "points_count": coll_info.points_count,
            "vectors_count": coll_info.vectors_count,
            "embedding_model": EMBEDDING_MODEL_NAME
        }
    except Exception as e:
        return {
            "status": "connection_error",
            "message": str(e),
            "connected": False
        }
