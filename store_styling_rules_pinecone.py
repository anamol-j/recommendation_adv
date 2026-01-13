import json
import torch
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# ------------------------------------
# CONFIG
# ------------------------------------
PINECONE_API_KEY = ""
INDEX_NAME = "styling-rules"
DATA_FILE = "fashion_data_enhanced_optimized_no_orig.json" 
# Or: "fashion_data_enhanced_optimized_no_orig.json"

# HuggingFace embedding model (1024 dimensions)
MODEL_NAME = "BAAI/bge-large-en-v1.5"

# ------------------------------------
# INIT CLIENTS
# ------------------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)

# load 1024-dim HF embedding model
print("Loading HuggingFace embedding model...")
model = SentenceTransformer(MODEL_NAME)

# ------------------------------------
# CREATE INDEX IF NOT EXISTS
# ------------------------------------
if INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index '{INDEX_NAME}' (1024 dimensions)...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

index = pc.Index(INDEX_NAME)

# ------------------------------------
# LOAD DATA
# ------------------------------------
def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

if DATA_FILE.endswith(".jsonl"):
    dataset = list(load_jsonl(DATA_FILE))
else:
    dataset = load_json(DATA_FILE)

print(f"Loaded {len(dataset)} styling rule entries.")

# ------------------------------------
# EMBEDDING FUNCTION
# ------------------------------------
def embed_text(text):
    vec = model.encode(text, convert_to_tensor=True)
    return vec.cpu().tolist()  # 1024-dim vector

# ------------------------------------
# UPSERT INTO PINECONE
# ------------------------------------
batch = []
batch_size = 50

print("Uploading vectors to Pinecone...")

for item in tqdm(dataset):

    vector = embed_text(item["text"])  # HF embeddings

    record = {
        "id": item["id"],
        "values": vector,
        "metadata": {
            "type": item["type"],
            "text": item["text"]
        }
    }

    batch.append(record)

    # batch upload
    if len(batch) >= batch_size:
        index.upsert(vectors=batch)
        batch = []

# upload remaining
if batch:
    index.upsert(vectors=batch)

print("\n✨ Upload complete — styling rules successfully stored in Pinecone!")
print("Index:", INDEX_NAME)
