from backend.scenario_editor import run_excel_agent
from backend.rag_agent import query_rag
import os

def process_instruction(instruction, input_file=None, mode="excel"):
    if mode == "excel":
        """Wrapper that calls the backend Excel modification pipeline."""
        output_file = os.path.join("data/outputs", os.path.basename(input_file).replace(".xlsx", "-updated.xlsx"))

        result = run_excel_agent(
            instruction=instruction,
            input_file=input_file,
            output_file=output_file
        )

        return {
            "mode": "excel",
            "output_file": output_file,
            "code": result["code"],
            "logs": result["logs"],
        }

    elif mode == "rag":
        # Directly query the RAG agent
        answer = query_rag(instruction)
        return {
            "mode": "rag",
            "answer": answer
        }

    else:
        raise ValueError("Invalid mode. Choose 'excel' or 'rag'.")    

