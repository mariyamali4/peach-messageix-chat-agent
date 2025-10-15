import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import streamlit as st

INDEX_PATH = "rag_store/faiss_hnsw_index.faiss"
META_PATH = "rag_store/rag_metadata.parquet"
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
