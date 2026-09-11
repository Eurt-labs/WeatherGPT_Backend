import os
import sys
import glob
import uuid
import re
from typing import List, Dict, Any
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding

QDRANT_URL = os.getenv("QDRANT_URL", "").strip().rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "weathergpt_rag").strip()
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIMENSION = 384

# Candidate paths for the RAG documents repository
RAG_PATHS = [
    BASE_DIR.parent / "WeatherGPT_RAG",
    BASE_DIR / "WeatherGPT_RAG",
    Path("C:/Users/Dhruv Saraswat/Documents/SIh/WeatherGPT_RAG")
]

def find_rag_root() -> Path:
    for p in RAG_PATHS:
        if p.exists() and (p / "agriculture").exists():
            return p
    raise FileNotFoundError(f"Could not find WeatherGPT_RAG folder in any of: {[str(p) for p in RAG_PATHS]}")

def chunk_markdown_file(file_path: Path, sector: str) -> List[Dict[str, Any]]:
    """Split a markdown file into logical sections by headers."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    doc_title = file_path.stem.replace("_", " ").title()
    chunks = []
    current_header = doc_title
    current_lines = []

    for line in lines:
        header_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if header_match:
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if len(chunk_text) > 40:
                    chunks.append({
                        "sector": sector,
                        "filename": file_path.name,
                        "title": f"{doc_title} — {current_header}",
                        "content": chunk_text
                    })
                current_lines = []
            current_header = header_match.group(2).strip()
        else:
            current_lines.append(line)

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if len(chunk_text) > 40:
            chunks.append({
                "sector": sector,
                "filename": file_path.name,
                "title": f"{doc_title} — {current_header}",
                "content": chunk_text
            })

    if not chunks and content.strip():
        chunks.append({
            "sector": sector,
            "filename": file_path.name,
            "title": doc_title,
            "content": content.strip()
        })

    return chunks

def main():
    print("==========================================================")
    print("  WeatherGPT RAG Knowledge Base Ingestion Engine")
    print("==========================================================")

    if not QDRANT_URL or not QDRANT_API_KEY:
        print("\n[!] Notice: QDRANT_URL or QDRANT_API_KEY is not configured yet in .env")
        print("Please edit .env in WeatherGPT_Backend and add:")
        print("  QDRANT_URL=https://your-cluster-id.cloud.qdrant.io:6333")
        print("  QDRANT_API_KEY=your-qdrant-api-key")
        print("\nAfter adding them, rerun: python scripts/ingest_rag.py")
        sys.exit(1)

    rag_root = find_rag_root()
    print(f"[*] Found RAG Knowledge Base at: {rag_root}")

    sectors = [
        "agriculture",
        "disaster_management",
        "india_regional",
        "meteorology_core",
        "urban_mobility",
        "aviation_cargo"
    ]

    all_chunks = []
    for sector in sectors:
        sector_dir = rag_root / sector
        if not sector_dir.exists():
            continue
        md_files = list(sector_dir.glob("*.md"))
        sector_chunk_count = 0
        for md_file in md_files:
            file_chunks = chunk_markdown_file(md_file, sector)
            all_chunks.extend(file_chunks)
            sector_chunk_count += len(file_chunks)
        print(f"  + {sector.ljust(22)}: {len(md_files)} files -> {sector_chunk_count} chunks")

    print(f"\n[*] Total Chunks to Ingest: {len(all_chunks)}")

    # Initialize FastEmbed
    print(f"\n[*] Loading FastEmbed model ({EMBEDDING_MODEL_NAME})...")
    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    # Initialize Qdrant Client
    print(f"[*] Connecting to Qdrant Cloud at: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30.0)

    # Ensure collection exists
    existing_collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in existing_collections:
        print(f"[*] Creating Qdrant collection '{QDRANT_COLLECTION}' (size={VECTOR_DIMENSION}, Cosine)...")
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=VECTOR_DIMENSION,
                distance=models.Distance.COSINE
            )
        )
    else:
        print(f"[*] Qdrant collection '{QDRANT_COLLECTION}' already exists.")

    try:
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="sector",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
    except Exception:
        pass

    # Generate Embeddings in batch
    print("\n[*] Generating vector embeddings for all chunks...")
    texts_to_embed = [
        f"{c['title']} | Sector: {c['sector']}\n{c['content']}"
        for c in all_chunks
    ]
    vectors = list(embedding_model.embed(texts_to_embed))

    # Prepare Qdrant Points
    points = []
    NAMESPACE_UUID = uuid.UUID("a2345678-1234-5678-1234-567812345678")
    for idx, (chunk, vec) in enumerate(zip(all_chunks, vectors)):
        point_id = str(uuid.uuid5(NAMESPACE_UUID, f"{chunk['sector']}:{chunk['filename']}:{idx}"))
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vec.tolist(),
                payload={
                    "title": chunk["title"],
                    "sector": chunk["sector"],
                    "filename": chunk["filename"],
                    "content": chunk["content"]
                }
            )
        )

    # Upload in batches
    BATCH_SIZE = 50
    print(f"[*] Uploading {len(points)} points to Qdrant Cloud in batches of {BATCH_SIZE}...")
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i:i + BATCH_SIZE]
        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=batch,
            wait=True
        )
        print(f"  Uploaded points {i + 1} to {min(i + BATCH_SIZE, len(points))}...")

    coll_info = client.get_collection(QDRANT_COLLECTION)
    print("\n==========================================================")
    print(f"[SUCCESS] Ingestion Complete! Collection '{QDRANT_COLLECTION}' now has {coll_info.points_count} points.")
    print("==========================================================")

if __name__ == "__main__":
    main()
