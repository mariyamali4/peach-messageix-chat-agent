# conv_history.py
import sqlite3, time
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "history" / "conv_history.db"

# --- Initialize database once ---
def init_db():
    '''
    Initialize the conversation history database and create the table if it doesn't exist.
    Output: None
    '''
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    conv_id TEXT,
                    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT,
                    routing_reason TEXT,
                    query TEXT NOT NULL,  
                    response TEXT,
                    output_file_name TEXT,
                    timestamp TEXT,
                    agent_execution_time REAL,
                    response_feedback INTEGER,
                    code_execution_retries_count INTEGER,
                    total_execution_time REAL,
                    error_flag INTEGER 
                )
            """)    
        print("✅ Conversation history database initialized.")
    except Exception as e:
        print("❌ Error initializing database:", e)


def log_turn(conv_id, mode, routing_reason, timestamp, query, response, agent_execution_time, code_execution_retries_count, error_flag, total_execution_time, output_file_name=None):
    ''' 
    Log a single turn in the conversation history.
    Inputs:
    - conv_id (str): Unique conversation ID
    - mode (str): 'rag' or 'scenario_editor'
    - routing_reason (str): Reason for choosing the agent (for debugging)
    - query (str): User's question or instruction
    - response (str): Assistant's response
    - output_file_name (str, optional): For Excel mode, the name of the output file
    - timestamp (str): ISO formatted timestamp
    Output: None

    Safely log a conversation turn with retry if DB is locked
    '''
    for attempt in range(5):
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_history
                    (conv_id, mode, routing_reason, query, response, output_file_name, timestamp, agent_execution_time, code_execution_retries_count, error_flag, total_execution_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (conv_id, mode, routing_reason, query, response, output_file_name, timestamp, agent_execution_time, code_execution_retries_count, error_flag, total_execution_time))
                conn.commit()
                
                inserted_turn_id = cursor.lastrowid
                print(f"✅ Logged turn {inserted_turn_id} for conversation {conv_id} in mode {mode}.")
                #print(f"🚨 ACTUAL DB PATH: {Path(DB_PATH).absolute()}") # ADD THIS LINE
                return inserted_turn_id
            break  
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                print(f"⚠️ Database is locked (attempt {attempt+1}/5). Retrying...")
                time.sleep(0.5)
            else:
                raise
    else:
        raise RuntimeError("❌ Database remained locked after 5 retries.")



def get_conversation(conv_id):
    '''
    Retrieve chat history for a given conversation ID.
    Input: conv_id (str)
    Output: List of tuples (turn_id, mode, routing_reason, query, response, output_file_name, timestamp)
    '''
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT turn_id, mode, routing_reason, query, response, output_file_name, timestamp
            FROM conversation_history
            WHERE conv_id = ?
           -- ORDER BY turn_id ASC
        """, (conv_id,)).fetchall()
    return rows


def new_conversation():
    '''
    Create a new unique conversation ID for each session.
    Output: conv_id (str) - first 13 characters/2 chunks of a UUID
    '''
    conv_id = str(uuid.uuid4())[:13]  # 
    return conv_id
