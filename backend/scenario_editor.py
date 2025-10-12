import pandas as pd
import re
import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY1"])
model = genai.GenerativeModel("gemini-2.5-flash")

def run_excel_agent(instruction, input_file, output_file, max_retries=1):
    """
    Reads Excel, gets transformation code from model, executes it safely, saves new file.
    Returns structured output for front-end.
    """
    logs = []
    df_input = pd.read_excel(input_file)
    logs.append("📄 Loaded Excel file successfully.")
    logs.append(f"Columns: {list(df_input.columns)}")

    # Prepare prompt
    prompt = f"""
        You are a data engineer for climate scenarios.
        Given this schema:
        Columns: {list(df_input.columns)}

        Example Rows:
        {df_input.head().values.tolist()}

        Instruction: {instruction}

        Write Python (pandas) code to apply this transformation.
        The DataFrame is named `df`.
        Return only the code, without any explanation or markdown formatting.
    """

    def generate_code(extra_context=None):
        context = prompt
        if extra_context:
            context += f"\nFix the issue described here: {extra_context}"
        response = model.generate_content(context)
        return re.sub(r"^```(?:python)?|```$", "", response.text.strip(), flags=re.MULTILINE).strip()

    # First attempt
    code = generate_code()
    logs.append("🧠 Model-generated code:")
    logs.append(code)

    # Safety checks
    forbidden_patterns = [
        r"import\s", 
        r"os\.", r"sys\.", r"open\s*\(", r"subprocess",
        r"eval\s*\(", r"exec\s*\(", r"__", r"shutil", r"pathlib"
    ]
    if any(re.search(p, code, re.IGNORECASE) for p in forbidden_patterns):
        print(code)
        raise ValueError("⚠️ Unsafe code detected! Execution blocked.")

    # Try executing
    for attempt in range(max_retries + 1):
        try:
            local_env = {"df": df_input.copy(), "pd": pd}
            exec(code, {}, local_env)
            df_new = local_env.get("df")

            if not isinstance(df_new, pd.DataFrame):
                raise ValueError("No valid DataFrame 'df' produced.")

            df_new.to_excel(output_file, index=False)
            logs.append(f"✅ Saved updated file to {output_file}")
            return {"success": True, "code": code, "logs": "\n".join(logs)}

        except Exception as e:
            logs.append(f"❌ Error executing code: {e}")
            if attempt < max_retries:
                logs.append("🔁 Retrying with fix...")
                code = generate_code(extra_context=str(e))
            else:
                return {"success": False, "code": code, "logs": "\n".join(logs)}
