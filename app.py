# app2.py
import streamlit as st
import os
import sqlite3
import pandas as pd
from backend.orchestrator_agent import orchestrate
from backend.conv_history import new_conversation

st.set_page_config(page_title="🍑 Peach+", layout="wide")
st.title("🍑 Peach - Message_ix Chat Agent")

# Create two tabs: Chat, Tracking Database/Files
tab_chat, tab_debug = st.tabs(["💬 Chat", "🛠️ Debug Dashboard"])

with st.sidebar:
    st.header("Scenario Settings")
    uploaded_file = st.file_uploader("📤 Upload scenario Excel file", type=["xlsx"])
    input_file_path, uploaded = None, False

    if uploaded_file:
        uploaded = True
        os.makedirs("data/history/uploads", exist_ok=True)
        os.makedirs("data/history/outputs", exist_ok=True)

        input_path = os.path.join("data/history/uploads", uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ File uploaded: {uploaded_file.name}")

# ---------- SESSION SETUP ----------
# Chat Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Conversation ID generated for each browser session (Refreshed when page reloaded)
if "conv_id" not in st.session_state:
    st.session_state.conv_id = new_conversation()

# ---------- 1. RENDER CHAT IN CHAT TAB ----------
with tab_chat:
    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

        # Re-render UI elements (like code blocks) if they exist in history
            if "code" in msg:
                with st.expander("🤖 Generated Code"):
                    st.code(msg["code"], language="python")


# ---------- 2. RENDER HISTORY IN DEBUG TAB ----------
with tab_debug:
    st.header("🛠️ System Internals")
    
    # --- 1. VIEW DATABASE (SQLite) ---
    st.subheader("📜 Conversation History (SQLite)")
    try:        
        db_path = os.path.join("data", "history", "conv_history.db") 
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            df_history = pd.read_sql_query("SELECT * FROM conversation_history", conn)
            st.dataframe(df_history, use_container_width=True)
            conn.close()
        else:
            st.info("No database file found yet. Start a chat to create one!")
    except Exception as e:
        st.error(f"Error reading DB: {e}")

    st.divider()

    # --- 2. VIEW SERVER FILES ---
    st.subheader("📁 Files on Server")
    
    # Helper to list files in your key directories
    for folder in ["data/history/uploads", "data/history/outputs"]:
        st.write(f"**Folder: `{folder}`**")
        if os.path.exists(folder):
            files = os.listdir(folder)
            if files:
                for file in files:
                    file_size = os.path.getsize(os.path.join(folder, file)) / 1024
                    st.text(f"📄 {file} ({file_size:.2f} KB)")
            else:
                st.caption("Empty folder.")
        else:
            st.caption("Folder not yet created.")


# ---------- 3. CHAT INPUT (OUTSIDE TABS) ----------
user_input = st.chat_input("Type your instruction or question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
 
    with tab_chat:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("⏳ Processing..."):
                try:
                    result = orchestrate(
                        instruction=user_input,
                        input_file=input_path if uploaded_file else None,
                        conv_id=st.session_state.conv_id
                    )

                    # ---------- DISPLAY ----------
                    assistant_reply = result["reply"]
                    st.markdown(assistant_reply)
                    reply_data = {"role": "assistant", "content": assistant_reply}


                    if result.get("code"):
                        with st.expander("🤖 Generated Code"):
                            st.code(result["code"], language="python")
                        reply_data["code"] = result["code"] # Save for re-renders

                    if result.get("logs"):
                        with st.expander("📜 Execution Logs"):
                            st.text(result["logs"])

                    if result.get("output_file"):
                        st.download_button(
                            "⬇️ Download Updated Scenario",
                            data=open(result["output_file"], "rb"),
                            file_name=os.path.basename(result["output_file"]),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    st.session_state.messages.append(reply_data)

                except Exception as e:
                    error_message = f"❌ Error: (app.py) {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})


