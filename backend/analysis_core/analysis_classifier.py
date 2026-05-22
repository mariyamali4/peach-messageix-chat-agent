#analysis_classifier.py
import os
from groq import Groq

groq_api_key = os.environ.get("GROQ_API_KEY1")
client = Groq(api_key=groq_api_key)


def _llm_classify(user_input):
    prompt = f"""
    `Role:`
    You are a classifier inside an energy-model analysis system (MESSAGEix/IAM).

    `Task:`
    Classify the user's query into exactly one of three analysis types:\n
    1. "direct_answer" — The user asks a precise, specific question about a particular metric, technology, trend, or time period.\n
    2. "mini_report" — The user asks for a broad, open-ended analysis, summary, or explanation of the scenario without targeting a specific metric.\n
    3. "visual_report" — The user is explicitly asking to generate, draw, or compile plots/visuals, with no analytical question attached.\n

    `Examples:`

    User: "Are emission trends rising after mid-century?"
    Output: "direct_answer"

    User: "Which technology dominates after 2040"
    Output: "direct_answer"

    User: "Analyse the uploaded scenario for me"
    Output: "mini_report"

    User: "Give me an overview of the energy mix"
    Output: "mini_report"

    User: "Generate these plots"
    Output: "visual_report"

    User: "Draw the selected plots"
    Output: "visual_report"

    User: "I want the selected plots for the uploaded scenario"
    Output: "visual_report"

    User query: "{user_input}"
    Respond ONLY with one of these analysis types: [direct_answer, mini_report, visual_report]
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        resp = completion.choices[0].message.content.strip().strip('"').lower()
        valid = {"direct_answer", "mini_report", "visual_report"}
        return resp if resp in valid else None  # reject anything unexpected
    except Exception as e:
        print(f"[Analysis Classifier Warning] LLM call failed: {e}")
        return None
    


def get_analysis_type(user_input, plot_list = None):
    """
    Classifies the analysis intent into one of four types:
    - visual_report:         user only wants selected plots compiled (no analysis query)
    - direct_answer:         precise, specific question targeting a metric or trend
    - mini_report:           open-ended, general analysis request
    - visual_direct_report:  direct answer + selected plots together
    - visual_mini_report:    mini report + selected plots

    plot_list: plots selected from the sidebar. None or empty means no visuals requested.
    """
    has_plots = bool(plot_list)

    # No text query, just plots
    if has_plots and not user_input.strip():
        return "visual_report"

    # Classify the text query via LLM
    llm_result = _llm_classify(user_input)
    if llm_result is None:
        llm_result = "mini_report"
    
    if has_plots and llm_result == "direct_answer":
        return "visual_direct_report"
    
    elif has_plots and llm_result == "mini_report":
        return "visual_mini_report"
    elif has_plots and llm_result == "visual_report":
        return "visual_report"

    return llm_result



# Local Testing
# user_input = "which emission categories contribute most to the rise in emissions after 2040"
# plot_list = ["co2 emission by demand sector", "co2 emission by energy supply"]
# get_analysis_type(user_input, plot_list)