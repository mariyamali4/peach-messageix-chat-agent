"""
Intent Detection Module
Routes user queries between 'scenario-editor' and 'rag-agent'
based on intent classification — using a rule-based method
with an optional LLM fallback. Now supports 'multi' flow for sequential tasks.
"""
import os
import json
from groq import Groq

groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key = groq_api_key)


def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    return json.loads(text)


def llm_route(user_input: str, chat_history: list = None):
    """
    LLM-based classification. 
    Can extract sub-queries for multi-intents (RAG -> Scenario Editor).
    """
    if chat_history is None:
        chat_history = []

    few_shot_prompt = f"""
        `Role:`
        You are an Agent Router in a multi-agent system. Choose between three states:
        1. "scenario_editor" — edits Excel data according to user instructions.
        2. "rag" — retrieves or explains information from a knowledge base.
        3. "multi" — User explicitly asks to BOTH retrieve information AND edit data sequentially in the same prompt.
        4. "analysis" - User asks you questions related to analysing or explaining a message scenario or an IAM scenario.
        5. "run_model" — User explicitly asks to run the model with the current scenario data, or solve the uploaded scenario.

        `Examples`:
        User: formulas and variables related to fix_cost, inv_cost, var_cost
        Output: {{"selected_agent": "rag", "reason": "User is asking for information.", "sub_queries": null}}

        User: make the inv_cost half
        Output: {{"selected_agent": "scenario_editor", "reason": "User is modifying Excel data values.", "sub_queries": null}}

        User: "rename the column 'investment_cost' to 'inv_cost' and save the file"
        Output: {{"selected_agent": "scenario_editor", "reason": "Explicit data transformation.", "sub_queries": null}}

        User: "what is the current solar investment cost? find it and then double it"
        Output: {{"selected_agent": "multi", "reason": "Requires finding information first, then editing it.", "sub_queries": {{"rag_query": "what is the current solar investment cost?", "scenario_query": "double the solar investment cost"}}}}

        User: "how much does wind cost? actually, just halve it in the sheet"
        Output: {{"selected_agent": "multi", "reason": "User asks for a value and also requests to modify it.", "sub_queries": {{"rag_query": "how much does wind cost?", "scenario_query": "halve the wind cost in the sheet"}}}}

        User: "which technology is historically the cheapest?"
        Output: {{"selected_agent": "rag", "reason": "User is asking for information."}}

        User: "should i edit the expensive technologies after 2050 to reduce costs?"
        Output: {{"selected_agent": "rag", "reason": "Asking for advice/information, not giving an edit command.", "sub_queries": null}}

        User: "explain this scenario"
        Output: {{"selected_agent": "analysis", "reason": "User wants to get explanation about a message_ix scenario.", "sub_queries": null}}

        User: "analyse the uploaded scenario for me"
        Output: {{"selected_agent": "analysis", "reason": "User wants to get analysis of a message_ix scenario.", "sub_queries": null}}

        User: "generate the selected plots"
        Output: {{"selected_agent": "analysis", "reason": "User wants to generate plots for the scenario.", "sub_queries": null}}

        User: "are emission trends rising after mid-century?"
        Output: {{"selected_agent": "analysis", "reason": "User asks a specific trend question about the scenario.", "sub_queries": null}}

        User: "which technology dominates the electricity mix by 2040?"
        Output: {{"selected_agent": "analysis", "reason": "User asks a specific question about the scenario.", "sub_queries": null}}

        User: "solve this scenario"
        Output: {{"selected_agent": "run_model", "reason": "User wants to solve the scenario using message_ix model.", "sub_queries": null}}

        User: "run the model with the current scenario data"
        Output: {{"selected_agent": "run_model", "reason": "User wants to execute the model.", "sub_queries": null}}

        `Task`
        Decide which agent should handle the given input: "{user_input}".
        Recent Chat History (for context/pronoun resolution): {chat_history}

        `Output format` 
        STRICTLY as JSON:
        If single intent (rag OR scenario_editor):
        {{"selected_agent": "<agent_name>", "reason": "<short explanation>", "sub_queries": null}}

        If multi-intent (BOTH information retrieval AND data editing):
        {{"selected_agent": "multi", 
         "reason": "<short explanation>",
         "sub_queries": {{
             "rag": "<the retrieval part of the prompt>",
             "scenario": "<the data editing part of the prompt>"
         }}
        }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b", # May bump to 70b if parsing sub_queries gets complex
            messages=[
                {
                    "role": "user",
                    "content": few_shot_prompt
                }
            ]
        )
        resp = completion.choices[0].message.content.strip()
        parsed = extract_json(resp)
        
        # Safety fallback if LLM forgets the sub_queries key
        if "sub_queries" not in parsed:
            parsed["sub_queries"] = None
            
        return parsed
    except Exception as e:
        print(f"[Router Warning] LLM routing failed: {e}")
        return None



def get_intent(user_input, chat_history = None):
    print("Checking intent...")
    """
    Route a user input to the appropriate sub-agent, using an LLM
    """
    llm_result = llm_route(user_input, chat_history)
    print(llm_result)
    return llm_result



# Local testing
# import time
# start = time.time()
# #r = get_intent("what is the cost of solar? find it and double it in the sheet", 
# r = get_intent("solve this scenario") 
# # r = get_intent("double the cost of wind if it's less than that", 
# #                chat_history=[
# #                     {"role": "user", "content": "what is the current solar investment cost?"},
# #                     {"role": "system", "content": "$123"}
# #                 ])
# end = time.time()
# print(json.dumps(r, indent=2))
# print(f"Execution time: {end - start} seconds")
