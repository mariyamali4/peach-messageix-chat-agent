# analysis_interpretation_layer.py
import re
import json
import pandas as pd
import numpy as np
import os
from groq import Groq


groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key=groq_api_key)

YEAR_COLS = [2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060, 2070]


# --------------------------------------------------------------------------------------
# STEP 1 — RESEARCH DIRECTOR
# --------------------------------------------------------------------------------------

def research_director(scenario_summary, user_query, chat_history=None):
    """
    First LLM call. Acts as a research director.
    Receives the compact scenario profile and user query.
    Returns Python code that computes the specific metrics needed to answer the query.
    The code will be executed against the raw DataFrame in the next step.
    """
    chat_history = chat_history or []

    prompt = f"""
    `Role:`   
        You are a data scientist acting as a research director who analyzes an IAM (Integrated Assessment Model) energy scenario, 
        and provides high-level guidance on which metrics to compute. 
    
    
    `Task:`
        You have been given a compact summary of the scenario and a user query.Your job is to identify the key variables and trends that are 
        relevant to the user's query and write Python code to calculate the relevant metrics, which will be executed against the raw DataFrame.

    `Context:`
        SCENARIO SUMMARY:
        {scenario_summary}

        USER QUERY:
        {user_query}

        CHAT HISTORY:
        {chat_history}

    `RULES:`
        - You have access to a pandas DataFrame called `df` with columns: {YEAR_COLS} + ['Model', 'Region', 'Scenario', 'Unit', 'Variable']
        - You may only use pandas and numpy
        - IAMC variables are hierarchical (e.g., 'Emissions|CO2'). Do NOT assume exact aggregate rows like 'Emissions' or 'Capacity' exist. 
        - To get totals, filter using `df["Variable"].str.startswith("Emissions")` and then sum the results across the year columns.
        - Store your final results in a dict called `results`
        - Do not import anything, do not print anything, do not write to disk
        - Return ONLY the Python code, no explanation, no markdown backticks

    `Example output:`
        # Safely get total CO2 emissions by summing sub-variables
        co2_df = df[df["Variable"].str.startswith("Emissions|CO2")]
        co2_totals = co2_df[{YEAR_COLS}].sum(axis=0)
        
        results = {{
            "co2_2050": float(co2_totals[2050]),
            "co2_trend": co2_totals.tolist()
        }}

    `OUTPUT FORMAT`:
        - Return ONLY valid Python code
        - No explanations
        - No markdown
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Research Director Warning] LLM call failed: {e}")
        return "results = {'error': 'LLM call failed: " + str(e) + "'}"



# --------------------------------------------------------------------------------------
# STEP 2 — DATA MANIPULATION (sandboxed execution)
# --------------------------------------------------------------------------------------

def run_code_sandbox(code, df):
    """
    Executes the Research Director's code against the raw DataFrame.
    Inputs: 
    - code (str), 
    - df (DataFrame)
    Output:
    - results (dict) — the computed metrics that will be passed to the synthesis LLM
    """
    # Strip markdown fences if the LLM ignored instructions
    code = re.sub(r"```(?:python)?|```", "", code).strip()

    forbidden_patterns = r"(?:os\.|sys\.|open\s*\(|subprocess|eval\s*\(|exec\s*\(|__|shutil|pathlib)"
    if re.search(forbidden_patterns, code, re.IGNORECASE):
        print(code)
        raise ValueError("⚠️ Unsafe code detected! Execution blocked.")
    

    import_lines = re.findall(r"^\s*import\s+[^\n]+", code, flags=re.MULTILINE)
    for line in import_lines:
        if not any(pkg in line for pkg in ["numpy", "pandas"]):
            raise ValueError(f"⚠️ Unsafe import detected: '{line.strip()}' — only numpy and pandas are allowed.")
        
    df_sandbox = df.copy()
    # For every integer year column, duplicate it as a string column name to avoid KeyErrors if the LLM generates code for string column names
    for col in [2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060, 2070]:
        if col in df_sandbox.columns:
            df_sandbox[str(col)] = df_sandbox[col]

    sandbox = {
        "df": df_sandbox,
        "pd": pd,
        "np": np,
        "results": {}  # the code writes into this
    }
    try:
        exec(code, sandbox)
    except Exception as e:
        return {"error": str(e)}
    
    results = sandbox.get("results", {})
    return results


# --------------------------------------------------------------------------------------
# STEP 3 — SYNTHESIS
# --------------------------------------------------------------------------------------

def synthesize(computed_results, user_query, 
               analysis_type_specific_task ="Explaining the scenario, highlighting things like key trends and insights"):
    """
    Second LLM call. Receives only the deterministically computed metrics.
    Focuses purely on narrative — no data processing here.
    Returns a plain-language explanation tailored to the audience.
    """
    prompt = f"""
    `Role:` You are an energy policy analyst explaining an IAM scenario to the audience specified in user_query.\n

    `Task:` 
        - {analysis_type_specific_task}
        - If the user_query isn't very specific, provide an analysis based on ALL the available variables and use ALL the relevant metrics.  
        - Write the analysis in reasonable detail based on the provided data, but do not speculate beyond the numbers you have.
        - If no user role is specified, assume the audience is a policymaker with basic familiarity with energy concepts but no technical expertise.
    

    `Context:`
        USER QUERY:
        {user_query}

        COMPUTED METRICS:
        {computed_results}


    `Response Format`:
        - Write clearly for the specified audience, avoiding raw jargon unless necessary.
        - Ground every claim in the numbers provided, do not speculate beyond them.
        - DO NOT mention use of metrics or intermediate calculations, just use them to support your analysis.
        - DO NOT start the response by repeating the user query. Start directly with the analysis.
        - Never use very large font sizes for headings, with the maximum heading size being H4.
        - Summarize the key points in a TL;DR format at the end. Title this section "Summary", with H4 heading, and DO NOT mention any other headings in this section.
    """

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}]
    )

    return completion.choices[0].message.content.strip()


# --------------------------------------------------------------------------------------
# interpretation_layer wrapper
# --------------------------------------------------------------------------------------

def run_interpretation_layer(df, scenario_summary, user_query, chat_history=None, max_retries=3):
    """
    Research Director → Data Manipulation → Synthesis
    Inputs:
        - df (DataFrame): the raw IAMC scenario DataFrame
        - scenario_summary (str): the compact JSON summary of the scenario for LLM context generated by intake layer
        - user_query (str): the user's natural language query
        - chat_history (list): optional list of previous user and assistant messages for context
        - max_retries (int): number of retries for self-healing code generation
    Output:
        - analysis_report (str): the final plain-language analysis to return to the user

    Self-healing pipeline:
    1. Research Director identifies relevant metrics and returns code (loops on failure)
    2. Code is executed safely against the raw DataFrame in a sandbox
    3. On error, the traceback message is fed back to the LLM to auto-correct
    4. Synthesis LLM explains the final verified results in plain language
    """
    logs = []
    error_context = None

    # analysis_type = direct-answer
    analysis_type_specific_task = "You have been given pre-computed metrics that directly answer the user's query. Your job is to explain what these numbers mean in plain language."

    # Steps 1 & 2 — Self-healing code generation and execution loop
    for attempt in range(max_retries + 1):
        if attempt > 0:
            current_query = f"{user_query}\n\nPREVIOUS GENERATED PYTHON SCRIPT FAILED WITH THIS ERROR:\n`{error_context}`\nPlease review the error and rewrite the code using .str.contains() or .str.startswith() to prevent KeyErrors."
        else:
            current_query = user_query

        # Step 1 - Research Director
        code = research_director(scenario_summary, current_query, chat_history)
        
        logs.append(f"--- [Attempt {attempt + 1}/{max_retries + 1}] Generated Code ---")
        logs.append(code)
        logs.append("-" * 20)
        print(code)
        print("-" * 20)


        # Step 2 - Data Manipulation
        computed_results = run_code_sandbox(code, df)

        # Check for sandboxed runtime errors
        if "error" in computed_results:
            error_context = computed_results["error"]
            logs.append(f"❌ Attempt {attempt + 1} failed: {error_context}")
            print(f"❌ Attempt {attempt + 1} failed: {error_context}")
            
            if attempt == max_retries:
                logs.append("🚨 Max retries reached. Pipeline failed.")
                return f"Unable to compute the requested metrics after {max_retries} correction attempts. Error: {error_context}"
            
            logs.append("🔁 Feeding exception context back to Research Director for auto-correction...")
            continue
        
        # If no error key is found, calculation succeeded
        logs.append(f"✅ Calculation successful on attempt {attempt + 1}!")
        break

    print("\n".join(logs))  
    formatted_metrics = json.dumps(computed_results, indent=2)

    # Step 3 - Synthesis
    analysis_report = synthesize(formatted_metrics, user_query, analysis_type_specific_task)

    return analysis_report, attempt




# ------------------------------------------ LOCAL TESTING ----------------------------------------------------------------------------
# import time

# user_query = "explain this scenario to me"
# input_file = r"D:\lums-python-programming\thesis\project\data\analysis-knowledgebase\MESSAGEix-Pakistan_baseline_2026-03-17--11-37.xlsx"
# user_query = "what do the emission trends and technology trends look like in this scenario?"

# start = time.time()
# df = pd.read_excel(input_file)

# from analysis_intake_layer import build_scenario_summary
# data_summary = build_scenario_summary(input_file)
# print(run_interpretation_layer(df, data_summary, user_query))

# print("Execution time:", time.time() - start)