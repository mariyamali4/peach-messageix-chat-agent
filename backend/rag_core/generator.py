from google import generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY1"))

def generate_answer(query, context, docTitles, llm_model_name="gemini-2.5-flash"):
  
    prompt = f"""
        You are a helpful assistant specialized in climate scenario modeling.
        Use only the following context to answer the user’s question as precisely as possible.

        Context:
        {context}

        Question:
        {query}

        Source:
        {docTitles}

        If the text contains math notation, format your response in a readable way for user. 
        Mention the source document titles at the end of the answer.
    """
    llm = genai.GenerativeModel(llm_model_name)
    resp = llm.generate_content(prompt)
    return resp.text
