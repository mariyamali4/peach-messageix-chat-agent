# orchestrator_agent2.py
import os
from datetime import datetime, timezone, timedelta
import time
from pathlib import Path

from backend.config.rag_config import load_rag_resources
from backend.conv_history import init_db, log_turn

from backend.intent_detection import get_intent
from backend.scenario_editor import run_scenario_agent
from backend.rag_engine import query_rag
from backend.analysis_agent import run_analysis_agent
from backend.run_msg_model import solve_message_scenario

# Cached load: only runs once when app starts
embedding_model, index, metadata = load_rag_resources()
# Ensure DB is ready once
init_db()

PKT = timezone(timedelta(hours=5))

BASE_DIR = Path(__file__).resolve().parents[1]
base_scenario_path = BASE_DIR / "data" / "docs" / "MESSAGEix-Pakistan-CurPol.xlsx"

def scenario_editor_wrapper(instruction, chat_history, input_file, timestamp, uploaded, output_file):
    if input_file is None:
        input_file = base_scenario_path
    output_file = os.path.join(
            "data/history/scenario_editor_outputs",
            os.path.basename(input_file).replace(".xlsx", f"-updated-{timestamp}.xlsx")
            )        
    
    result = run_scenario_agent(
        instruction, 
        chat_history, 
        input_file, 
        uploaded, 
        output_file, 
        embedding_model, index, metadata
    )
    
    reply = f"✅ Scenario updated: `{os.path.basename(output_file)}`"
    code = result.get("code")
    logs = result.get("logs")
    error_flag = result.get("error_flag", 0)
    agent_execution_time = result.get("agent_execution_time", None)
    code_execution_retries_count = result.get("retries") if result.get("retries") else 0

    return result


def rag_wrapper(instruction, chat_history):
    result = query_rag(instruction, 
                            chat_history, 
                            embedding_model, index, metadata
                        )
    reply = result.get("reply", "")
    summary = result.get("summary", "")
    error_flag = result.get("error_flag", 0)
    agent_execution_time = result.get("agent_execution_time", None)

    return result


def analysis_wrapper(instruction, input_file, timestamp, chat_history, plots_list):
    if input_file is None:
            reply = "No file attached for analysis"

    else:
        result = run_analysis_agent(instruction, 
                                    input_file,
                                    timestamp,
                                    chat_history, 
                                    plots_list
                            )
        reply = result.get("reply", "")
        summary = result.get("summary", "")
        error_flag = result.get("error_flag", 0)
        agent_execution_time = result.get("agent_execution_time", None)
        output_file = result.get("report", None)
        code_execution_retries_count = result.get("code_retries") if result.get("code_retries") else 0
    return result

def run_model_wrapper(input_file, output_file, timestamp):
    if input_file is None:
            input_file = base_scenario_path
            print("No input file provided for model run, using default:", input_file)
    output_file = os.path.join(
            "data/history/msg_scenario_outputs",
            os.path.basename(input_file).replace(".xlsx", f"-updated-{timestamp}.xlsx")
            )        
    
    result = solve_message_scenario(
        input_file,
        output_file
        # chat_history
    )
    error_flag = result.get("error_flag", 0)
    obj_val = result.get("objective_value", None)

    if error_flag==0:
        print("\n\nModel solved successfully! Objective value:", obj_val)
        reply = f"""
        Model Solved Successfully! \n
        Objective Value: {obj_val}\n
        Solved Scenario File: `{os.path.basename(output_file)}`
        """
    else:
        reply = f"❌ Model run failed. Check logs for details."
    return result


def orchestrate(instruction, input_file=None, conv_id=None, chat_history=None, pipeline_start_time=0.0, plot_options=None):
    """
    Central orchestration layer:
    - intent detection
    - agent routing
    - DB logging
    """
    start_time = time.time()
    print("ORCHESTRATE CALLED WITH:", repr(instruction))

    uploaded = input_file is not None
    timestamp = datetime.now(PKT).strftime("%Y%m%d-%H%M%S")
    code_execution_retries_count = 0

    # Initiliase new conv_id if conv_id is not passed from app.py
    if conv_id is None:
        from backend.conv_history import new_conversation
        conv_id = new_conversation()

    if (plot_options and input_file) and not instruction.strip():
        mode, routing_reason = "analysis", "Plot options provided without text query, assuming visual report intent"
    else:
        routing = get_intent(instruction, chat_history)
        mode = routing.get("selected_agent")    
        routing_reason = routing.get("reason", "")      

    # 1. Initialize empty variables for the Single Exit Point
    reply, summary, code, logs, output_file = "", None, None, None, None

    # ---------- SCENARIO EDITOR ----------
    if mode == "scenario_editor":
        if input_file is None:
            input_file = base_scenario_path
        output_file = os.path.join(
                "data/history/scenario_editor_outputs",
                os.path.basename(input_file).replace(".xlsx", f"-updated-{timestamp}.xlsx")
                )        
        
        result = run_scenario_agent(
            instruction, 
            chat_history, 
            input_file, 
            uploaded, 
            output_file, 
            embedding_model, index, metadata
        )
        
        reply = f"✅ Scenario updated: `{os.path.basename(output_file)}`"
        code = result.get("code")
        logs = result.get("logs")
        error_flag = result.get("error_flag", 0)
        agent_execution_time = result.get("agent_execution_time", None)
        code_execution_retries_count = result.get("retries") if result.get("retries") else 0

    # ---------- RAG ----------
    elif mode == "rag":
        result = query_rag(instruction, 
                            chat_history, 
                            embedding_model, index, metadata
                            )
        reply = result.get("reply", "")
        summary = result.get("summary", "")
        error_flag = result.get("error_flag", 0)
        agent_execution_time = result.get("agent_execution_time", None)
        
        
    # ---------- ANALYSIS ----------
    elif mode == "analysis":
        if input_file is None:
            reply = "No file attached for analysis"

        else:
            result = run_analysis_agent(instruction, 
                                        input_file,
                                        timestamp,
                                        chat_history, 
                                        plots_list=plot_options
                                )
            reply = result.get("reply", "")
            summary = result.get("summary", "")
            error_flag = result.get("error_flag", 0)
            agent_execution_time = result.get("agent_execution_time", None)
            output_file = result.get("report", None)
            code_execution_retries_count = result.get("code_retries") if result.get("code_retries") else 0
        

    # ---------- RUN Model ----------
    elif mode == "run_model":
        if input_file is None:
            input_file = base_scenario_path
            print("No input file provided for model run, using default:", input_file)
        output_file = os.path.join(
                "data/history/msg_scenario_outputs",
                os.path.basename(input_file).replace(".xlsx", f"-updated-{timestamp}.xlsx")
                )        
        
        result = solve_message_scenario(
            input_file,
            output_file
            # chat_history
        )
        error_flag = result.get("error_flag", 0)
        obj_val = result.get("objective_value", None)

        if error_flag==0:
            print("\n\nModel solved successfully! Objective value:", obj_val)
            reply = f"""
            Model Solved Successfully! \n
            Objective Value: {obj_val}\n
            Solved Scenario File: `{os.path.basename(output_file)}`
            """
        else:
            reply = f"❌ Model run failed. Check logs for details."


    # ---------- MULTI-INTENT (RAG -> SCENARIO) ----------
    elif mode == "multi":
        sub_queries = routing.get("sub_queries") or {}
        rag_instruction = sub_queries.get("rag", instruction)
        scenario_instruction = sub_queries.get("scenario", instruction)
        
        input_file = input_file or base_scenario_path
        output_file = os.path.join(
                "data/history/scenario_editor_outputs",
                os.path.basename(input_file).replace(".xlsx", f"-updated-{timestamp}.xlsx")
            )

        # Execute RAG
        result = query_rag(rag_instruction, 
                            chat_history, 
                            embedding_model, index, metadata
                            )
        rag_reply = result.get("reply", "")
        summary = result.get("summary", "")
        error_flag = result.get("error_flag", 0)
        agent_execution_time = result.get("agent_execution_time", None)
        
        # Execute Scenario
        enriched_instruction = f"Based on this retrieved information: '{summary}', execute this user request: {scenario_instruction}"
        result = run_scenario_agent(enriched_instruction, 
                                    chat_history, 
                                    input_file, 
                                    uploaded, 
                                    output_file, 
                                    embedding_model, index, metadata)
        
        reply = f"**Information Found:**\n{rag_reply}\n\n**Action Taken:**\n✅ Scenario updated: `{os.path.basename(output_file)}`"
        code = result.get("code")
        logs = result.get("logs")
        error_flag = result.get("error_flag", 0)
        code_execution_retries_count = result.get("retries", 0)
        agent_execution_time2 = result.get("agent_execution_time", None)
        agent_execution_time+=agent_execution_time2 if agent_execution_time and agent_execution_time2 else None

    else:
        raise ValueError(f"Unknown agent mode: {mode}")


    # ================ SINGLE EXIT POINT (Logging and Returning) =======================

    end_time = time.time()
    execution_time = round((end_time - start_time), 2)

    # Format the reply for the database
    stored_reply = reply
    if code:
        stored_reply += f"\n\nGenerated code:\n{code}"
    

    db_formatted_timestamp = f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
    total_execution_time = round((end_time - pipeline_start_time), 2) if pipeline_start_time else 0.0
    error_flag=error_flag if error_flag is not None else 0

    inserted_turn_id = log_turn(
        conv_id=conv_id,
        mode=mode,
        routing_reason=routing_reason,
        timestamp=db_formatted_timestamp,
        query=instruction,
        response=stored_reply,
        agent_execution_time=execution_time,
        code_execution_retries_count=code_execution_retries_count if code_execution_retries_count else 0,
        error_flag=error_flag,
        total_execution_time=total_execution_time,
        output_file_name=os.path.basename(output_file) if output_file else None
    )

    return {
        "mode": mode,
        "reply": reply,
        "summary": summary if summary else None,
        "output_file": output_file if output_file else None,
        "code": code if code else None,
        "logs": logs if logs else None,
        "timestamp": timestamp,
        "turn_id": inserted_turn_id,
        "error_flag": error_flag,
        "total_execution_time": total_execution_time
    }