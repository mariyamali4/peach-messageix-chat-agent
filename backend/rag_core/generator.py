import os
from groq import Groq


groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key = groq_api_key)

def generate_answer(query, context, docTitles, llm_model_name="openai/gpt-oss-120b"):
    '''
    Generate answer using LLM given the query and context chunks.
     Inputs:
        - query (str): User's question or instruction
        - context (str): Retrieved document chunks as context
        - docTitles (str): Titles of the source documents
        - llm_model_name (str): Name of the LLM model to use
     Outputs:
        - answer (str): Generated answer from the LLM
        - output_file (str or None): Name of output file if mentioned in answer
    '''
  
    prompt = f"""
        You are a helpful assistant specialized in climate scenario modeling.
        Use only the following context to answer the user’s question as precisely as possible.

        Context:
        {context}

        Question:
        {query}

        Source:
        {docTitles}

        Make sure to format math notation in your response in a readable way for user. Never print unformatted math notation.
        Mention the source document titles at the end of the answer.
    """

    completion = client.chat.completions.create(
            model=llm_model_name, 
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    response = completion.choices[0].message.content

    return response


    # Iterate over the response chunks and print/process them as they arrive, when stream = True in completion creation
    # for chunk in chat_completion:
    #     print(chunk.choices[0].delta.content or "", end="")
    # print("\n") # Add a final newline for clean output
