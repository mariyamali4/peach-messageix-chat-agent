# app.py
import streamlit as st
import os
import time
import sqlite3
import pandas as pd
from backend.orchestrator_agent import orchestrate
from backend.conv_history import new_conversation, DB_PATH

import base64

def show_pdf_inline(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def format_chat_history(raw_messages):
    """
    Transforms the full Streamlit UI history into a lightweight payload for the LLM.
    Returns: 
    - Past 2 conversation turns for context (to manage token limits)
    - User queries, 
    - Assistant Logs (Scenario), 
    - Assistant Summary (RAG), 
    - Feedback
    """
    formatted_history = []
    for msg in raw_messages:
        role = msg.get("role")
        
        if role == "user":
            formatted_history.append({
                "role": "user", 
                "content": msg.get("content")
            })
            continue
            
        if role == "assistant":
            context_parts = []
            
            feedback = msg.get("response_feedback")
            if feedback is not None:
                feedback_text = "Positive" if feedback == 1 else "Negative"
                context_parts.append(feedback_text)

            if msg.get("summary"):
                context_parts.append(f"Summary of Response: {msg['summary']}")
            if msg.get("logs"):
                context_parts.append(f"Execution Logs:\n{msg['logs']}")
            if (msg.get("summary") is None) and (msg.get("logs") is None):
                context_parts.append(f"Excerpt from the response: {msg.get('content')[:300]}")  # Truncate if no summary/logs
            formatted_history.append({
                "role": "assistant", 
                "content": "\n".join(context_parts)
            })
            
    return formatted_history


st.set_page_config(page_title="🍑 Peach+", layout="wide")
st.title("🍑 Peach - Message_ix Chat Agent")

# Create two tabs: Chat, Tracking Database/Files
tab_chat, tab_debug = st.tabs(["💬 Chat", "🛠️ Debug Dashboard"])

with st.sidebar:
    st.header("Uploads")
   # uploaded_file = st.file_uploader("📤 Upload scenario Excel file", type=["xlsx"], accept_multiple_files=True)
    uploaded_file = st.file_uploader("📤 Upload scenario Excel file", type=["xlsx"])

    input_file_path, uploaded = None, False

    if uploaded_file:
        uploaded = True
        os.makedirs("data/history/scenario_editor_uploads", exist_ok=True)
        os.makedirs("data/history/scenario_editor_outputs", exist_ok=True)

        input_path = os.path.join("data/history/scenario_uploads", uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ File uploaded: {uploaded_file.name}")


    show_plots = st.sidebar.checkbox("Show Analytics Plots Options")
    plots = [
        'ALL',
        'emission kyto gases',
        'electricity generation mix',
        'final energy industry',
        'final energy residential commercial',
        'final energy transportation',
        'installed electricity capacity',
        'co2 emission by demand sector',
        'co2 emission by energy supply',
        'emissions by pollutant energy',
        'emissions by pollutant industrial processes',
        'emissions by pollutant waste',
        'total energy by fuel',
        'primary energy mix',
        'trade primary energy volumes',
        'trade secondary energy volumes',
        'resource extraction'
    ]
    if show_plots:
        plot_options = st.sidebar.multiselect(
            'Which plots do you want to draw?',
            plots
        )
        st.write('Selected Plots: ', plot_options)

# ---------- SESSION SETUP ----------
# Chat Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Conversation ID generated for each browser session (Refreshed when page reloaded)
if "conv_id" not in st.session_state:
    st.session_state.conv_id = new_conversation()

# Define DB Path
#db_path = os.path.join("data", "history", "conv_history.db") 
db_path = DB_PATH

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
                df_history = pd.read_sql_query("SELECT * FROM conversation_history ORDER BY turn_id DESC", conn)
                st.dataframe(df_history, use_container_width=True)
        else:
            st.info("No database file found yet. Start a chat to create one!")
    except Exception as e:
        st.error(f"Error reading DB: {e}")

    st.divider()


    # --- 2. VIEW SERVER FILES (Local Directories) ---
    st.subheader("📁 Files on Server")
    for folder in ["data/history/scenario_editor_uploads", "data/history/scenario_editor_outputs", "data/history/msg_scenario_uploads", "data/history/msg_scenario_outputs"]:
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
    pipeline_start_time = time.time()
    st.session_state.messages.append({"role": "user", "content": user_input})
 
    with tab_chat:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("⏳ Processing..."):
                try:
                    chat_length = len(st.session_state.messages[:-1])                                   # Count of previous messages except the current user input
                    recent_raw_history = st.session_state.messages[max(0, chat_length-4):chat_length]   # Get the last 4 messages (2 user-assistant pairs) for context
                    clean_history = format_chat_history(recent_raw_history)

                    plots_selected = plot_options if (show_plots and plot_options) else None
                    result = orchestrate(
                        instruction=user_input,
                        input_file=input_path if uploaded_file else None,
                        conv_id=st.session_state.conv_id,
                        chat_history=clean_history,
                        pipeline_start_time=pipeline_start_time,
                        plot_options=plots_selected
                    )

                    # ---------- DISPLAY ----------
                    assistant_reply = result["reply"]
                    st.markdown(assistant_reply)
                    
                    # turn_id for recording feedback
                    curr_turn_id = result['turn_id']  

                    reply_data = {
                        "role": "assistant", 
                        "content": assistant_reply,
                        "logs": result.get("logs") if result.get("logs") else None,
                        "summary": result.get("summary") if result.get("summary") else None,
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
                        output_path = result["output_file"]
                        file_name = os.path.basename(output_path)
                        
                        # Extract the extension to determine file type
                        _, file_extension = os.path.splitext(file_name)
                        file_extension = file_extension.lower()

                        # Set appropriate label and mime type based on extension
                        if file_extension == ".pdf":
                            show_pdf_inline(result["output_file"])
                            button_label = "⬇️ Download PDF Report"
                            mime_type = "application/pdf"
                        elif file_extension in [".xlsx", ".xls"]:
                            button_label = "⬇️ Download Updated Scenario"
                            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                        # Read and offer the file for download
                        with open(output_path, "rb") as file_to_download:
                            st.download_button(
                                label=button_label,
                                data=file_to_download,
                                file_name=file_name,
                                mime=mime_type
                        )

                    
                    if result.get("total_execution_time") is not None:
                        st.caption(f"{result['total_execution_time']}s")
                    

                    if result.get("summary"):
                        reply_data["summary"] = result["summary"]
                    
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


