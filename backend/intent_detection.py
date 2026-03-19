"""
Intent Detection Module
Routes user queries between 'scenario-editor' and 'rag-agent'
based on intent classification — using a rule-based method
with an optional LLM fallback.
"""
import os
import json
from groq import Groq

groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key = groq_api_key)

"""
Initialize the router.
use_llm: If True, enables LLM fallback for ambiguous cases.
edit_keywords, excel_terms: Keywords indicating editing intent.
question_words: Words indicating question/retrieval intent.
"""
use_llm = True

# edit_keywords = [
#     "make", "update", "change", "modify", "edit", "replace", "rename", "filter", "delete", "drop", "add", "remove", "save", "create",
#     "format", "convert", "read", "write", "output", "double", "halve", "increase", "decrease", "multiply", "divide"
# ]
excel_terms = ["excel", "sheet", "df", "dataframe", "pd", "column", "row"]
question_words = ["what", "which", "who", "where", "when", "why", "how", "is", "are", "does", "do", 
                  "should", "could", "would", "can"]


def rule_based_route(user_input):
    """
    Fast rule-based classification between agents.
    """
    if user_input:
        text = user_input.lower().strip()

        # Case 1: explicit edit / manipulation
       # if any(k in text for k in edit_keywords) or any(k in text for k in excel_terms):
        if any(k in text for k in excel_terms):
            if any(text.startswith(q + " ") for q in question_words):
                return {
                    "selected_agent": "rag",
                    "reason": "Question phrasing detected, likely information retrieval."
                }
            else:
                return {
                    "selected_agent": "scenario_editor",
                    "reason": "Contains edit or Excel manipulation keywords."
                }

        # Case 2: pure question or retrieval
        if any(text.startswith(q + " ") for q in question_words):
            return {
                "selected_agent": "rag",
                "reason": "Question form indicates retrieval or explanation query."
            }

    # Fallback: assume rag
    return {
        "selected_agent": "rag",
        "reason": "Defaulting to RAG agent (no edit indicators found)."
    }


def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    return json.loads(text)


def llm_route(user_input: str):
    """
    LLM-based classification (fallback or enhanced reasoning).
    """
    few_shot_prompt = f"""
        You are an Agent Router in a multi-agent system:
        1. scenario_editor — edits Excel data according to user instructions.
        2. rag-agent — retrieves or explains information from a knowledge base.

        
        Examples:
        User: formulas and variables related to fix_cost, inv_cost, var_cost
        Output: {{"selected_agent": "rag", "reason": "User is asking for information, not editing data."}}

        User: make the inv_cost half
        Output: {{"selected_agent": "scenario_editor", "reason": "User is modifying Excel data values."}}

        User: "rename the column 'investment_cost' to 'inv_cost' and save the file"
        Output: {{"selected_agent": "scenario_editor", "reason": " Explicit data transformation, so use the scenario-editor agent."}}

        User: "read the inv_cost sheet, format the data into a pd dataframe, and double the solar value. give the output in form of an excel file, with the relevant changes saved"
        Output: {{"selected_agent": "scenario_editor", "reason": "This requires reading, editing, and writing Excel data, so use the scenario-editor agent."}}

        User: "should i edit the expensive technologies after 2050 to reduce costs?"
        Output: {{"selected_agent": "rag", "reason": "The query is asking for information, not editing data."}}

        User: "which technology is historically the cheapest?"
        Output: {{"selected_agent": "rag", "reason": "User is asking for information."}}

        User: "how can i change inv_cost?"
        Output: {{"selected_agent": "rag", "reason": "User is asking for information, not giving direct edit instructions."}}

        Decide which agent should handle the given input: {user_input}. 

        In case of questions, pay attention to whether the user is seeking information (rag-agent),
        or requesting data edits (scenario-editor).

        Output format STRICTLY as JSON:
        {{"selected_agent": "rag" or "scenario_editor", 
         "reason": "<short explanation>"}}
    """
    
    try:
        completion = client.chat.completions.create(
          #  model="openai/gpt-oss-120b",
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": few_shot_prompt
                }
            ]
        )
        resp = completion.choices[0].message.content.strip()
        parsed = extract_json(resp)
        return parsed
    except Exception as e:
        print(f"[Router Warning] LLM routing failed: {e}")
        return None


def get_intent(user_input: str):
    print("Checking intent...")
    """
    Route a user input to the appropriate sub-agent.
    Automatically uses LLM fallback if enabled and available.
    """
    rule_result = rule_based_route(user_input)
    print(f"Rule-based result: {rule_result}")

    # If LLM mode is active, only invoke for uncertain or generic retrieval cases
    if use_llm and rule_result["selected_agent"] == "rag":
        print('Routing to LLM')
        llm_result = llm_route(user_input)
        print(llm_result)
        if llm_result:
            return llm_result

    return rule_result

## Local testing
# import time
# start = time.time()
#r = get_intent("should i remove the most expensive non-renewable technology after 2030")
#r = get_intent("how can i edit fixed cost?")
# r = get_intent("list down the sheet most relevant to this investment and triple the investment in solar after 2030")
# end = time.time()
# print(r['selected_agent'])
# print(f"Execution time: {end - start} seconds")
