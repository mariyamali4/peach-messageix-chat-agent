# orchestrator_agent.py
import os
from datetime import datetime, timezone, timedelta
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


def orchestrate(instruction, input_file=None, conv_id=None):
    print("ORCHESTRATE CALLED WITH:", repr(instruction))

    """
    Central orchestration layer:
    - intent detection
    - agent routing
    - DB logging
    """
    uploaded = input_file is not None
    timestamp = datetime.now(PKT).strftime("%Y%m%d-%H%M%S")

    # Initiliase new conv_id if conv_id is not passed from app.py
    if conv_id is None:
        from backend.conv_history import new_conversation
        conv_id = new_conversation()

    routing = get_intent(instruction)
    mode = routing["selected_agent"]
    routing_reason = routing.get("reason", "")

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
            input_file,
            uploaded,
            output_file,
            embedding_model, index, metadata
        )

        reply = f"✅ Scenario updated: `{os.path.basename(output_file)}`"

        stored_reply = (
            f"{reply}\n\n"
            f"Generated code:\n{result.get('code')}"
        )

        # ---- DB LOGGING ----
        inserted_turn_id = log_turn(
            conv_id=conv_id,
            mode=mode,
            routing_reason=routing_reason,
            timestamp=timestamp,
            query=instruction,
            response=stored_reply,
            output_file_name=os.path.basename(output_file)
        )

        return {
            "mode": mode,
            "reply": reply,
            "output_file": output_file,
            "code": result.get("code"),
            "logs": result.get("logs"),
            "timestamp": timestamp,
            "turn_id": inserted_turn_id
        }

    # ---------- RAG ----------
    elif mode == "rag":
       # reply = query_rag(instruction)
        reply = query_rag(instruction, embedding_model, index, metadata)

        inserted_turn_id = log_turn(
            conv_id=conv_id,
            mode=mode,
            routing_reason=routing_reason,
            timestamp=timestamp,
            query=instruction,
            response=reply,
            output_file_name=None
        )

        return {
            "mode": mode,
            "reply": reply,
            "timestamp": timestamp,
            "turn_id": inserted_turn_id
        }

    else:
        raise ValueError(f"Unknown agent mode: {mode}")
