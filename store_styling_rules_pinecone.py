import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

# Pinecone & embedder imports
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# -------------------------
# Configuration
# -------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY",'pcsk_5B19ud_MVAmfWe2zQEGzgfjooH3z2m3f1pjfoWpK5n8NDuk7bzeb6e4rX1u1cg24V2nsa8')
if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY environment variable is not set.")

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "styling-rules-index")
JSON_FILE = os.getenv("STYLING_JSON", "fashion_data_enhanced_full.json")  # file to read

# Embedding model
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
embedder = SentenceTransformer(MODEL_NAME)
VECTOR_DIM = embedder.get_sentence_embedding_dimension()

# Chunking parameters (tune as needed)
MAX_CHARS_PER_CHUNK = 800   # approx. chunk size for embeddings
CHUNK_OVERLAP = 50          # characters of overlap between chunks

BATCH_SIZE = 64             # number of texts to embed/upsert per batch

# -------------------------
# Utilities
# -------------------------
def read_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Case 1: already a list
    if isinstance(data, list):
        return data

    # Case 2: wrapped inside a key like {"rules": [...]}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                return value

        # Case 3: dict of rules keyed by IDs
        return [
            {"id": k, **v} if isinstance(v, dict) else {"id": k, "canonical_text": str(v)}
            for k, v in data.items()
        ]

    raise RuntimeError("Unsupported JSON structure for styling rules")


def ensure_id(rule: Dict[str, Any]) -> str:
    if rule.get("id"):
        return str(rule["id"])
    return str(uuid.uuid4())

def canonicalize_text(text: str) -> str:
    if text is None:
        return ""
    # simple canonicalization: normalize whitespace, strip control chars
    text = text.replace("\r", " ").replace("\n", " ").strip()
    text = " ".join(text.split())
    return text

def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        # try to extend to nearest sentence boundary within short range
        if end < len(text):
            # look for last sentence boundary in chunk
            last_dot = chunk.rfind('. ')
            if last_dot > int(max_chars * 0.5):
                end = start + last_dot + 1
                chunk = text[start:end]
        chunks.append(chunk.strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]

def build_text_for_embedding(rule: Dict[str, Any], chunk_text_piece: str = None) -> str:
    """
    Compose a text string to embed. Include canonical_text + tags + short source context.
    Keep short to avoid token explosion.
    """
    parts = []
    canonical = canonicalize_text(rule.get("canonical_text") or "")
    if chunk_text_piece:
        parts.append(chunk_text_piece)
    else:
        parts.append(canonical)
    # include small contextual signals to improve semantic density
    tags = rule.get("tags") or rule.get("metadata", {}).get("tags")
    if tags:
        if isinstance(tags, (list, tuple)):
            parts.append(" ".join([str(t) for t in tags]))
        else:
            parts.append(str(tags))
    src = rule.get("source")
    if src:
        parts.append(f"source:{src}")
    # confidence as signal (string appended)
    conf = rule.get("confidence")
    if conf is not None:
        try:
            parts.append(f"confidence:{float(conf):.2f}")
        except Exception:
            pass
    return " | ".join([p for p in parts if p])

def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms

# -------------------------
# Pinecone init & index ensure
# -------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = [i["name"] for i in pc.list_indexes()]

if INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index '{INDEX_NAME}'...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=VECTOR_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"Using existing Pinecone index '{INDEX_NAME}'.")

index = pc.Index(INDEX_NAME)

# -------------------------
# Load, validate, prepare vector documents
# -------------------------
raw_rules = read_json_file(JSON_FILE)
if not raw_rules:
    raise RuntimeError("No styling rules found in JSON file.")

print(f"Loaded {len(raw_rules)} rules from {JSON_FILE}")

# Prepare a list of items to embed (each item -> one Pinecone vector)
to_embed_items = []
for rule in raw_rules:
    rid = ensure_id(rule)
    canonical = canonicalize_text(rule.get("canonical_text") or rule.get("original_text") or "")
    if not canonical:
        # skip rules with no textual content
        continue

    # chunk long rules
    chunks = chunk_text(canonical)
    for idx, chunk in enumerate(chunks):
        vector_id = f"{rid}--chunk-{idx}"
        # keep metadata compact but informative
        metadata = {
            "original_id": rid,
            "chunk_index": idx,
            "source": rule.get("source"),
            "confidence": float(rule.get("confidence")) if rule.get("confidence") is not None else None,
            "tags": rule.get("tags") or rule.get("metadata", {}).get("tags"),
            "language": rule.get("language"),
            "created_at": rule.get("created_at") or datetime.utcnow().isoformat() + "Z",
            # store a short preview of the chunk for quick inspection
            "text_preview": chunk[:400]
        }
        text_for_embedding = build_text_for_embedding(rule, chunk_text_piece=chunk)
        to_embed_items.append({
            "id": vector_id,
            "text": text_for_embedding,
            "metadata": metadata
        })

print(f"Prepared {len(to_embed_items)} embedding items (after chunking).")

# -------------------------
# Batch embed, normalize, upsert
# -------------------------
def batch_generator(items: List[Dict[str, Any]], batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

total = len(to_embed_items)
upserted = 0

for batch in batch_generator(to_embed_items, BATCH_SIZE):
    texts = [item["text"] for item in batch]
    ids = [item["id"] for item in batch]
    metadatas = [item["metadata"] for item in batch]

    # create embeddings (numpy array)
    vectors = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # normalize to unit length (helps cosine search)
    vectors = l2_normalize(vectors)

    # build pinecone upsert batch
    pinecone_vectors = []
    for vid, vec, meta in zip(ids, vectors, metadatas):
        vec_list = vec.tolist()
        pinecone_vectors.append({
            "id": vid,
            "values": vec_list,
            "metadata": meta
        })

    # upsert
    index.upsert(vectors=pinecone_vectors)
    upserted += len(pinecone_vectors)
    print(f"Upserted {upserted}/{total}")

print("\n✅ Completed upsert to Pinecone.")
print(f"Index name: {INDEX_NAME}")
