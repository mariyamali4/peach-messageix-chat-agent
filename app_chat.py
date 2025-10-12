# app_chat.py
import streamlit as st
import os
from backend.main_agent import process_instruction

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🍑 Peach - Message_ix Chat", layout="wide")
st.title("🍑 Peach - Message_ix Chat Agent")

# ---------- MODE SELECTOR ----------
mode = st.radio("Select Agent Mode:", ["Scenario Editor", "Document Q&A (RAG)"])

# ---------- EXCEL MODE ----------
if mode == "Scenario Editor":
    st.markdown("Upload a scenario Excel file, and let's edit it together!")

    uploaded_file = st.file_uploader("📤 Upload your file", type=["xlsx"])

    if uploaded_file:
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("outputs", exist_ok=True)

        input_path = os.path.join("uploads", uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ File uploaded: {uploaded_file.name}")
    else:
        st.info("Please upload your file to start chatting.")
        st.stop()

# ---------- CHAT MEMORY ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------- USER INPUT ----------
user_input = st.chat_input("Type your instruction or question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("⏳ Processing..."):
            try:
                if mode == "Excel Editor":
                    result = process_instruction(user_input, input_path, mode="excel")

                    st.markdown("✅ Done! Here's what I did:")

                    with st.expander("🤖 Model-generated code"):
                        st.code(result["code"], language="python")

                    with st.expander("📜 Execution Logs"):
                        st.text(result["logs"])

                    output_path = result["output_file"]
                    st.download_button(
                        label="⬇️ Download Updated Excel",
                        data=open(output_path, "rb"),
                        file_name=os.path.basename(output_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                    reply = f"Updated Excel file ready: `{os.path.basename(output_path)}` ✅"

                else:  # RAG mode
                    result = process_instruction(user_input, mode="rag")
                    reply = result["answer"]

                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                error_message = f"❌ Error: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
