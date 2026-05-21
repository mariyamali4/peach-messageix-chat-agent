#rag_engine.py
from backend.rag_core.retriever import retrieve_chunks
from backend.rag_core.generator import generate_answer

import time


def query_rag(query, chat_history, embedding_model, index, metadata):
    """Run the RAG pipeline: retrieve → generate → return answer"""

    start_time = time.time()
    try:
        results = retrieve_chunks(query, embedding_model, index, metadata, k=5, for_rag=True)
        texts = [text for text in results["body"]]
        docs = "\n\n".join(texts)
        docTitles = list(set(results['docTitle']))
        reply, summary = generate_answer(query, chat_history, docs, docTitles)

        end_time = time.time()
        execution_time = round((end_time - start_time), 2)

      #  return reply, summary
        return {"error_flag": 0, 
                "reply": reply, 
                "summary": summary, 
                "agent_execution_time": execution_time
                }
    
    except Exception as e:
        print("Error in RAG pipeline:", e)
        end_time = time.time()
        execution_time = round((end_time - start_time), 2)
        return {"error_flag": 1, 
                "reply": None, 
                "summary": None, 
                "agent_execution_time": execution_time
                }



