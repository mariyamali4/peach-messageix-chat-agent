#analysis_agent
import os
import pandas as pd
from groq import Groq
import time
import matplotlib.pyplot as plt

from backend.analysis_core.analysis_plots import plot_wrapper
from backend.analysis_core.analysis_classifier import get_analysis_type
from backend.analysis_core.analysis_intake_layer import build_scenario_summary
from backend.analysis_core.analysis_interpretation_layer import synthesize, run_interpretation_layer
from backend.analysis_core.pdf_report_generator import build_pdf_report

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


def run_analysis_agent(user_query, input_file, timestamp=None, chat_history=None, plots_list=None):
    output_file_path = "data/history/scenario_analysis_outputs"
    
    start_time = time.time()
    def execution_time():
        return round((time.time() - start_time), 2)

    def error_response(msg):
        return {"reply": msg, 
                "summary": None, 
                "report": None, 
                "error_flag": 1, 
                "agent_execution_time": execution_time()
                }

    analysis_type = get_analysis_type(user_query, plots_list)

    if analysis_type == "visual_report":
        try:
            output_pdf=f'{output_file_path}/Analysis_Visual_Report_{timestamp}.pdf'
            figures_list = plot_wrapper(plots_list, input_file, output_pdf)
            agent_execution_time = round((time.time() - start_time), 2)
            return {
                "reply": f"✅ Visual report generated: `{output_pdf}`",
                "summary": None,
                "report": output_pdf,
                "error_flag": 0,
                "agent_execution_time": agent_execution_time,
            }
        except Exception as e:
            print("Error in visual_report generation:", e)
            return error_response("❌ Failed to generate visual_report.")
        

    elif analysis_type == "mini_report":
        # If user wants a general analysis, we provide the entire scenario summary as context, and ask for broad insights, trends, and explanations.
        try:
            _, scenario_summary = build_scenario_summary(input_file)
            analysis_report = synthesize(scenario_summary, user_query)
            report_summary = extract_summary(analysis_report)
            agent_execution_time = round((time.time() - start_time), 2)
            return {
                "reply": analysis_report,
                "summary": report_summary,
                "report": None,
                "error_flag": 0,
                "agent_execution_time": agent_execution_time,
            }
        except Exception as e:
            print("Error in mini_report generation:", e)
            return error_response("❌ Failed to generate mini_report.")
        

    elif analysis_type == "direct_answer":
        # If user asks a specific question, we still provide the scenario summary as context, but prompt the LLM to focus on directly answering the specific query.
        try:
            df, scenario_summary = build_scenario_summary(input_file)
            analysis_report = run_interpretation_layer(df, scenario_summary, user_query)
            report_summary = extract_summary(analysis_report)
            agent_execution_time = round((time.time() - start_time), 2)
            return {
                "reply": analysis_report,
                "summary": report_summary,
                "report": None,
                "error_flag": 0,
                "agent_execution_time": agent_execution_time,
            }
        except Exception as e:
            print("Error in direct_answer generation:", e)
            return error_response("❌ Failed to generate direct_answer.")

    elif analysis_type == "visual_direct_report":
        # If user asks a specific question and selects plots, we still run the interpretation pipeline to get the analysis, then generate plots, and then compile everything into a PDF report.
        try:
            df, scenario_summary = build_scenario_summary(input_file)
            analysis_report = run_interpretation_layer(df, scenario_summary, user_query)
            report_summary = extract_summary(analysis_report)

            output_pdf=f'{output_file_path}/Analysis_Visual_Report_{timestamp}.pdf'
            figures_list = plot_wrapper(plots_list, input_file, "temp-plots.pdf")
            build_pdf_report(analysis_report, figures_list, output_pdf)

            # Closing the figures to free up memory 
            for fig in figures_list:
                plt.close(fig)

            agent_execution_time = round((time.time() - start_time), 2)
            return {
                "reply": analysis_report,
                "summary": report_summary,
                "report": output_pdf,
                "error_flag": 0,
                "agent_execution_time": agent_execution_time,
            }
        except Exception as e:
            print("Error in visual_direct_report generation:", e)
            return error_response("❌ Failed to generate visual_direct_report.")
    

    elif analysis_type == "visual_mini_report":
        # If user asks a general question and selects plots, we still run the synthesize function to get the analysis, then generate plots, and then compile everything into a PDF report.
        try:
            _, scenario_summary = build_scenario_summary(input_file)
            analysis_report = synthesize(scenario_summary, user_query)
            report_summary = extract_summary(analysis_report)

            output_pdf=f'{output_file_path}/Analysis_Visual_Report_{timestamp}.pdf'
            figures_list = plot_wrapper(plots_list, input_file, "temp-plots.pdf")
            build_pdf_report(analysis_report, figures_list, output_pdf)

            # Closing the figures to free up memory 
            for fig in figures_list:
                plt.close(fig)

            agent_execution_time = round((time.time() - start_time), 2)
            return {
                "reply": analysis_report,
                "summary": report_summary,
                "report": output_pdf,
                "error_flag": 0,
                "agent_execution_time": agent_execution_time,
            }
        except Exception as e:
            print("Error in visual_mini_report generation:", e)
            return error_response("❌ Failed to generate visual_mini_report.")

    else:
        return {
                "reply": f"❌ Could not classify analysis type.",
                "summary": None,
                "report": None,
                "error_flag": 1,
                "agent_execution_time": None
            }
    
    