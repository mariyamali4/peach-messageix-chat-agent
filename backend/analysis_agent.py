# #analysis_agent
# import os
# import pandas as pd
# from groq import Groq
# from pathlib import Path
# import time
# from analysis_core.analysis_plots import plot_wrapper


# groq_api_key = os.environ.get("GROQ_API_KEY1")
# client = Groq(api_key = groq_api_key)

# BASE_DIR = Path(__file__).resolve().parents[1]
# variable_definitions_path = BASE_DIR / "data" / "analysis-knowledgebase" / "default_variable_definitions.csv"


# def get_analysis_intent(query):
#     analysis_intents =["direct_answer", "mini-report", "visual-report", "full-report"]
#     pass



# def run_analysis_agent(query, input_file, timestamp=None, chat_history=None, plots_list=None):
#     start_time = time.time()
#     analysis_intent = get_analysis_intent(query)

#     if analysis_intent == "visual-report":
#         try:
#             output_pdf=f'Analysis_Visual_Report_{timestamp}.pdf'
#             plot_wrapper(plots_list, input_file, output_pdf)
#             agent_execution_time = round((time.time() - start_time), 2)
#             return {
#                 "reply": f"✅ Visual report generated: `{output_pdf}`",
#                 "summary": None,
#                 "report:": output_pdf,
#                 "error_flag": 0,
#                 "agent_execution_time": agent_execution_time
#             }
#         except Exception as e:
#             print("Error in visual report generation:", e)
#             agent_execution_time = round((time.time() - start_time), 2)
#             return {
#                 "reply": f"❌ Failed to generate visual report.",
#                 "summary": None,
#                 "report:": None,
#                 "error_flag": 1,
#                 "agent_execution_time": agent_execution_time
#             }
    
