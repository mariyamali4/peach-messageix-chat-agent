import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import google.generativeai as genai

# ---------- CONFIG ----------
genai.configure(api_key=os.environ["GEMINI_API_KEY1"])

DOCS_DIR = Path("data/docs")
CHROMA_DIR = Path("data/chroma_index")

# ---------- BUILD ----------
def build_rag_index():
    """Builds a Chroma index from all DOCX files in data/docs/."""
    print("📚 Building new Chroma index from documents...")

    docs = []
    for file in DOCS_DIR.glob("*.docx"):
        loader = Docx2txtLoader(str(file))
        docs.extend(loader.load())

    if not docs:
        raise FileNotFoundError("No .docx files found in data/docs/. Please add one before querying.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    # ✅ Local embeddings (no API credentials needed)
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    db = Chroma.from_documents(chunks, embeddings, persist_directory=str(CHROMA_DIR))
    db.persist()
    print(f"✅ Chroma index built and saved to {CHROMA_DIR}")
    return db


# ---------- LOAD OR BUILD ----------
def load_or_build_index():
    """Loads Chroma index if it exists, otherwise builds it."""
    if CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()):
        print("📦 Loading existing Chroma index...")
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        return Chroma(persist_directory=str(CHROMA_DIR), embedding_function=embeddings)
    else:
        return build_rag_index()


# ---------- QUERY ----------
def query_rag(query):
    """Query the RAG system."""
    db = load_or_build_index()
    docs = db.similarity_search(query, k=3)
    context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
    You are a helpful assistant specialized in climate scenario modeling.
    Use only the following context to answer the user’s question as precisely as possible.

    Context:
    {context}

    Question:
    {query}
    """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

