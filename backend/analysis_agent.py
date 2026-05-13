import os
import pandas as pd
from groq import Groq
from pathlib import Path


groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key = groq_api_key)

BASE_DIR = Path(__file__).resolve().parents[1]
variable_definitions_path = BASE_DIR / "data" / "analysis-knowledgebase" / "default_variable_definitions.csv"

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



def generate_analysis(query, chat_history, input_file, 
                    #  llm_model_name="openai/gpt-oss-120b"
                      llm_model_name = "meta-llama/llama-4-scout-17b-16e-instruct"):
    '''
    Generate answer using LLM given the query and context chunks.
     Inputs:
        - query (str): User's question or instruction
        - chat_history (list): List of previous messages in the conversation
        - input_file (str): Path of the input_file for the scenario
        - llm_model_name (str): Name of the LLM model to use
     Outputs:
        - answer (str): Generated answer from the LLM
    '''
  
    df_input = pd.read_excel(input_file)

    # Joining variable definition column with uploaded file data
    # def_df = pd.read_csv(variable_definitions_path)
    # unique_def_df = def_df.drop_duplicates(subset=['Variable'], keep='first')
    # def_mapping = unique_def_df.set_index('Variable')['Definition']
    # df_input['variable_definition'] = df_input['Variable'].map(def_mapping)

    prompt = f"""
        `Role`:
        You are a helpful assistant specialized in climate scenario analysis.\n
        You are experienced at analyzing scenarios for intergrated assessment models, especially MESSAGEix, and providing an explanation of what the scenario represents.

        `TASK`:
         - Read the provided message_ix (integrated assessment model) data in the IAMC format.
         - Provide an explanation/analysis of the scenario in a language and format suitable for policymakers rather than your research colleagues.
         - If the user asks what affects any changes in the scenario may yield, answer that considering MESSAGEix model.
         - At the end of the response, provide a TL;DR summary which sums up all the information in the response.
         
        `Input Artifacts:`
         - The schema of the IAMC format scenario file.\n 
         - The IAMC format scenario in the format of a dictionary. \n
         - An excerpt of chat history is provided for additional context, in order to help with user's follow-up questions. If the chat history is empty or irrelevant, completely disregard it.\n
         - If the instructions are not clear, do not make any assumptions, and ask the user for clarification.

        `Schema:`
        {list(df_input.columns)}

        `Data rows:`
        {df_input.head(100).to_csv(index=False)}

        `User's Query:`
        {query}

        History of conversation:
        {chat_history}


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
    """
    print(prompt)

    completion = client.chat.completions.create(
            model=llm_model_name, 
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens= 2000
        )
    response = completion.choices[0].message.content
    summary = extract_summary(response)

    return response, summary

# query = "what does this scenario represent"
# chat_history =""
# input_file = r"D:\lums-python-programming\thesis\project\data\analysis-knowledgebase\MESSAGEix-Pakistan_baseline_2026-03-17--11-37.xlsx"
# r, s = generate_answer(query, chat_history, input_file)
# print(f"Response: {r}, \n\nSummary: {s}")

