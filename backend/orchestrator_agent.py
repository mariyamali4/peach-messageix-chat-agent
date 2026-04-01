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

# Cached load: only runs once when app starts
embedding_model, index, metadata = load_rag_resources()
# Ensure DB is ready once
init_db()

PKT = timezone(timedelta(hours=5))

BASE_DIR = Path(__file__).resolve().parents[1]
base_scenario_path = BASE_DIR / "data" / "docs" / "MESSAGEix-Pakistan-CurPol.xlsx"

def orchestrate(instruction, input_file=None, conv_id=None, chat_history=None):
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

    # Initiliase new conv_id if conv_id is not passed from app.py
    if conv_id is None:
        from backend.conv_history import new_conversation
        conv_id = new_conversation()

    routing = get_intent(instruction, chat_history)
   # mode = routing.get("selected_agent", "rag")  
    mode = routing.get("selected_agent")    
    routing_reason = routing.get("reason", "")      

    # 1. Initialize empty variables for the Single Exit Point
    reply, summary, code, logs, output_file = "", None, None, None, None

    # ---------- SCENARIO EDITOR ----------
    if mode == "scenario_editor":
        if input_file is None:
            input_file = base_scenario_path
        output_file = os.path.join(
                "data/history/outputs",
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

    # ---------- RAG ----------
    elif mode == "rag":
        reply, summary = query_rag(instruction, 
                                   chat_history, 
                                   embedding_model, index, metadata
                                   )

    # ---------- MULTI-INTENT (RAG -> SCENARIO) ----------
    elif mode == "multi":
        sub_queries = routing.get("sub_queries") or {}
        rag_instruction = sub_queries.get("rag", instruction)
        scenario_instruction = sub_queries.get("scenario", instruction)
        
        input_file = input_file or base_scenario_path
        output_file = os.path.join(
                "data/history/outputs",
                os.path.basename(input_file).replace(".xlsx", f"-updated-{timestamp}.xlsx")
            )

        # Execute RAG
        rag_reply, summary = query_rag(rag_instruction, 
                                       chat_history, 
                                       embedding_model, index, metadata
                                       )
        
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

    else:
        raise ValueError(f"Unknown agent mode: {mode}")


    # ================ SINGLE EXIT POINT (Logging and Returning) =======================

    end_time = time.time()
    execution_time = round((end_time - start_time), 2)

    # Format the reply for the database
    stored_reply = reply
    if code:
        stored_reply += f"\n\nGenerated code:\n{code}"

    inserted_turn_id = log_turn(
        conv_id=conv_id,
        mode=mode,
        routing_reason=routing_reason,
        timestamp=timestamp,
        query=instruction,
        response=stored_reply,
        execution_time=execution_time,
        output_file_name=os.path.basename(output_file) if output_file else None
    )

    return {
        "mode": mode,
        "reply": reply,
        "summary": summary if summary else None,
        "output_file": output_file,
        "code": code if code else None,
        "logs": logs if logs else None,
        "timestamp": timestamp,
        "turn_id": inserted_turn_id,
        "execution_time": execution_time
    }