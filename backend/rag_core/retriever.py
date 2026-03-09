import faiss


def retrieve_chunks(query, embedding_model, index, metadata, k=8, for_rag=False):
    '''
    Retrieve the top-k relevant document chunks from FAISS index for a given query based on semantic similarity,
    get their metedata from metadata store, and return as a DataFrame.
    
    Inputs:
        - query (str): user query 
        - embedding_model (str): EMBEDDING_MODEL
        - index: FAISS index, acting as vector store
        - metadata: metadata store, accompanying the FAISS index
        - k (int): no. of top similar chunks to retrieve
        - for_rag (bool): whether retrieval is for RAG or other usecases
    Outputs:
        - results (pd.DataFrame): top-k relevant document chunks with metadata
    '''
    
    q_emb = embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    faiss.normalize_L2(q_emb)
    D, I = index.search(q_emb, k)             # D -> np array of similarities, I -> indices for rows stored in metadata
    results = metadata.iloc[I[0]].copy()
    results["similarity"] = D[0]
    results = results.sort_values("similarity", ascending=False).reset_index(drop=True)
    if for_rag:
        return results[["docTitle", "body"]]  # minimal for LLM
    return results