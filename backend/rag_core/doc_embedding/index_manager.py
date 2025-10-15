import faiss, pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta
from sentence_transformers import SentenceTransformer
from itertools import chain
from backend.rag_core.doc_embedding.docx_parser import docx_parse
from backend.rag_core.doc_embedding.xlsx_parser import excel_parse


# --- paths ---
BASE_DIR = Path(r"D:\lums-python-programming\thesis\project")
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
RAG_STORE_DIR = BASE_DIR / "rag_store"

RAG_STORE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

INDEX_PATH = RAG_STORE_DIR / "faiss_hnsw_index.faiss"
META_PATH  = RAG_STORE_DIR / "rag_metadata.parquet"

# --- configurations ---
EMBEDDING_MODEL = "intfloat/e5-small-v2"      
MAX_LEN_DOCX, MAX_LEN_XLSX = 1000, 2000
PKT = timezone(timedelta(hours=5))

def add_to_index():
    model = SentenceTransformer(EMBEDDING_MODEL)

    # === 1️. Load existing index + metadata if they exist ===
    if META_PATH.exists() and INDEX_PATH.exists():
        metadata = pd.read_parquet(META_PATH)
        index = faiss.read_index(str(INDEX_PATH))
        print(f"✅ Loaded existing index with {len(metadata)} records")
    else:
        metadata = pd.DataFrame(columns=["chunkId", "docTitle", "insertionDate", "body"])
        index = None
        print("🆕 No existing index found — creating new one")

    existing_docs = set(metadata["docTitle"]) if not metadata.empty else set()

    all_new_records, all_new_embs = [], []

    # === 2️. Process only NEW documents ===
    for path in chain(DOCS_DIR.glob("*.docx"), DOCS_DIR.glob("*.xlsx")):
        if path.name.startswith("~$") or path.name.startswith("."):
            continue
        if path.name in existing_docs:
            continue  # already indexed

        if path.suffix.lower() ==".docx":
            chunks = docx_parse(str(path), max_len=MAX_LEN_DOCX)
        else:
            chunks = excel_parse(str(path), max_len=MAX_LEN_XLSX)

        new_records = [{
            "chunkId": f"{path.stem}_{i:04d}",
            "docTitle": path.name,
            "insertionDate": datetime.now().isoformat(),
            "body": text
        } for i, text in enumerate(chunks)]

        new_embs = model.encode([r["body"] for r in new_records], convert_to_numpy=True)
        faiss.normalize_L2(new_embs)

        all_new_records.extend(new_records)
        all_new_embs.append(new_embs)
        print(f"➕ Added {len(chunks)} chunks from {path.name}")

    if not all_new_records:
        print("✅ No new documents found — index up to date")
        return

    new_embeddings = np.vstack(all_new_embs)
    new_metadata = pd.DataFrame(all_new_records)

    # === 3️. Add to existing index ===
    if index is None:
        dim = new_embeddings.shape[1]
        index = faiss.IndexHNSWFlat(dim, 32)
        index.hnsw.efSearch = 64
        index.add(new_embeddings)
    else:
        index.add(new_embeddings)

    # === 4️. Append metadata ===
    updated_metadata = pd.concat([metadata, new_metadata], ignore_index=True)
    # ensure 'body' column is always a string
    updated_metadata["body"] = updated_metadata["body"].apply(
        lambda x: "\n".join(x) if isinstance(x, (list, tuple)) else str(x)
    )
    updated_metadata.to_parquet(META_PATH)
    faiss.write_index(index, str(INDEX_PATH))
    print(f"✅ Index updated — total records: {len(updated_metadata)}")