import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
RAG_STORE_DIR = BASE_DIR / "rag_store"
INDEX_PATH = str(RAG_STORE_DIR / "faiss_hnsw_index.faiss")
META_PATH = str(RAG_STORE_DIR / "rag_metadata.parquet")

print(type(INDEX_PATH))

EMBEDDING_MODEL = "intfloat/e5-small-v2"

@st.cache_resource(show_spinner=False)
def load_rag_resources():
    """
    Loads and caches the embedding model, FAISS index, and metadata.
    Called once at Streamlit startup, reused across reruns.
    """
    model = SentenceTransformer(EMBEDDING_MODEL)
    index = faiss.read_index(INDEX_PATH)
    metadata = pd.read_parquet(META_PATH)

    return model, index, metadata
