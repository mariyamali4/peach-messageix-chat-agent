import os
from groq import Groq


groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key = groq_api_key)


def extract_summary(text):
        summary_lines = []
        found_summary = False
        
        for line in text.splitlines():
            if ("### Summary" in line) or ("### TL;DR" in line):
                found_summary = True
                continue
            if found_summary:
                if line.strip(): 
                    summary_lines.append(line)
                
        return "\n".join(summary_lines)



def generate_answer(query, chat_history, context, docTitles, llm_model_name="openai/gpt-oss-120b"):
    '''
    Generate answer using LLM given the query and context chunks.
     Inputs:
        - query (str): User's question or instruction
        - chat_history (list): List of previous messages in the conversation
        - context (str): Retrieved document chunks as context
        - docTitles (str): Titles of the source documents
        - llm_model_name (str): Name of the LLM model to use
     Outputs:
        - answer (str): Generated answer from the LLM
        - output_file (str or None): Name of output file if mentioned in answer
    '''
  
    prompt = f"""
        `Role`: You are a helpful assistant specialized in climate scenario modeling.

        `Task`:
        - Use only the provided context to answer the user’s question as precisely as possible. Refrain from making the response very elaborate, unless explicitly requested.
        - An excerpt of chat history is provided for additional context, in order to help with user's follow-up questions.
        - If the requested information is not contained in the provided context, do not make assumptions, and ask the user for clarification.
        - At the end of the response, provide a TL;DR summary which sums up all the information in the response, and mentions major keywords.

        `Context and Background`:
        Context:
        {context}

        History of conversation:
        {chat_history}

        `Question`:
        {query}

        `Source`:
        {docTitles}

        `MATHEMATICAL NOTATION RULES`:
        1. For standalone equations, wrap them in double dollar signs: $$ [equation] $$
        2. For inline math (like variables), wrap them in single dollar signs: $x$
        3. Use standard LaTeX syntax. Do NOT use double semicolons (;;) or unformatted text blocks.
        4. Ensure all symbols (like n, t, y) are explained clearly after the equation.

        `Response Format`:
        - Provide the answer in clear, concise language.
        - Never use very large font sizes for headings, with the maximum heading size being H4.
        - If you include any equations, format them using LaTeX as per the rules above.
        - Summarize the key points in a TL;DR format at the end. Title this section "Summary", with H4 heading.
        - Present the source documents in an appropriately formatted list at the end of the response.
    """
    print(prompt)

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
    summary = extract_summary(response)

    return response, summary
