#rag_engine.py
from backend.rag_core.retriever import retrieve_chunks
from backend.rag_core.generator import generate_answer


def query_rag(query, embedding_model, index, metadata):
    """Run the RAG pipeline: retrieve → generate → return answer"""
    results = retrieve_chunks(query, embedding_model, index, metadata, k=5, for_rag=True)
    texts = [text for text in results["body"]]
    docs = "\n\n".join(texts)
    docTitles = list(set(results['docTitle']))
    reply = generate_answer(query, docs, docTitles)

    return reply


