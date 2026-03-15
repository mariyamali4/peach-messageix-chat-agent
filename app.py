# app.py
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

# Define DB Path
db_path = os.path.join("data", "history", "conv_history.db") 

# ---------- 1. RENDER CHAT IN CHAT TAB ----------
with tab_chat:
    # Display previous messages
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Re-render code blocks if they exist in history
            if "code" in msg:
                with st.expander("🤖 Generated Code"):
                    st.code(msg["code"], language="python")

            # Re-draw the feedback button on page reload
            if msg["role"] == "assistant":
                sentiment_mapping = [":material/thumb_down:", ":material/thumb_up:"]
                selected_feedback = st.feedback("thumbs", key=f"fb_key_{i}")
                if selected_feedback is not None:
                    st.markdown(f"You selected: {sentiment_mapping[selected_feedback]}")
        
                    # Only update DB if the rating just changed or is new
                    if msg.get("response_feedback") != selected_feedback:
                        st.session_state.messages[i]["response_feedback"] = selected_feedback
                        
                        # Update DB
                        if os.path.exists(db_path):
                            with sqlite3.connect(db_path) as conn:
                                cursor = conn.cursor()
                                if "turn_id" in msg:
                                    cursor.execute(
                                        "UPDATE conversation_history SET response_feedback = ? WHERE turn_id = ?",
                                        (selected_feedback, msg["turn_id"])
                                    )
                                    conn.commit()
                                    st.toast("✅ Feedback recorded!")
                        else:
                            st.info("DB connection not available to record feedback.")


# ---------- 2. RENDER HISTORY IN DEBUG TAB ----------
with tab_debug:
    st.header("🛠️ System Internals")
    
    # --- 1. View Chat History (SQLite) ---
    st.subheader("📜 Conversation History (SQLite)")
    try:                
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                df_history = pd.read_sql_query("SELECT * FROM conversation_history ORDER BY timestamp DESC", conn)
                st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No database file found yet. Start a chat to create one!")
    except Exception as e:
        st.error(f"Error reading DB: {e}")

    st.divider()


    # --- 2. VIEW SERVER FILES (Local Directories) ---
    st.subheader("📁 Files on Server")
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
                    
                    # turn_id for recording feedback
                    curr_turn_id = result['turn_id']  

                    reply_data = {
                        "role": "assistant", 
                        "content": assistant_reply,
                        "turn_id": curr_turn_id,
                        "response_feedback": None
                    }
                    

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
                    
                    # FEEDBACK UI
                    current_msg_index = len(st.session_state.messages) 
                    sentiment_mapping = [":material/thumb_down:", ":material/thumb_up:"]
                    selected_feedback = st.feedback("thumbs", key=f"fb_key_{current_msg_index}")
                    
                    if selected_feedback is not None:
                       st.markdown(f"You selected: {sentiment_mapping[selected_feedback]}")
                    reply_data["response_feedback"] = selected_feedback 

                    st.session_state.messages.append(reply_data)

                except Exception as e:
                    error_message = f"❌ Error: (app.py) {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})


