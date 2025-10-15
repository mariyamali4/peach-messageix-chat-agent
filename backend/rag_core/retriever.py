import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

# --- configuration ---
BASE_DIR = Path(r"D:\lums-python-programming\thesis\project")
RAG_STORE_DIR = BASE_DIR / "rag_store"
RAG_STORE_DIR.mkdir(exist_ok=True)

INDEX_PATH = RAG_STORE_DIR / "faiss_hnsw_index.faiss"
META_PATH  = RAG_STORE_DIR / "rag_metadata.parquet"
EMBEDDING_MODEL = "intfloat/e5-small-v2"      # or "all-MiniLM-L6-v2"


def retrieve_chunks(query, model, index, metadata, k=10, for_rag=False):
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    faiss.normalize_L2(q_emb)
    D, I = index.search(q_emb, k)             # D -> np array of similarities, I -> indices for rows stored in metadata
    results = metadata.iloc[I[0]].copy()
    results["similarity"] = D[0]
    results = results.sort_values("similarity", ascending=False).reset_index(drop=True)
    if for_rag:
        return results[["docTitle", "body"]]  # minimal for LLM
    return results