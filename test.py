import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# ------------------------------------
# CONFIG
# ------------------------------------
PINECONE_API_KEY = ""
INDEX_NAME = "styling-rules"

# HuggingFace embedding model (1024 dimensions)
MODEL_NAME = "BAAI/bge-large-en-v1.5"

# ------------------------------------
# INIT CLIENTS
# ------------------------------------
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# ------------------------------------
# QUERY TEXT
# ------------------------------------
query = "Youthful trendy outfits for casual workout occasions, complementing natural features with regular fit clothing."

print(f"\n🔍 Query: {query}")

# embed
q_vec = model.encode(query).tolist()

# ------------------------------------
# RUN VECTOR SEARCH
# ------------------------------------
results = index.query(
    vector=q_vec,
    top_k=5,
    include_metadata=True
)

# ------------------------------------
# PRINT RESULTS
# ------------------------------------
print("\n🔥 Top Matches:")
for match in results["matches"]:
    print(f"\nID: {match['id']}")
    print(f"Score: {match['score']:.4f}")
    if "metadata" in match:
        print(f"Type: {match['metadata'].get('type')}")
        print(f"Text: {match['metadata'].get('text')}")
    print("-" * 40)
