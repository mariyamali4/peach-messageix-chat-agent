# 🍑 Peach-AgenticIAM — An LLM-Based Multi-Agent Framework for Interactive Integrated Assessment Modeling

**Peach** lets users:
1. **Edit MESSAGEix-style scenario Excel files** using natural-language instructions.
2. **Query supporting documentation** (e.g. messaeg_ix documentation files, current policy documents) using a robust RAG system.

Built with **Streamlit**, **FAISS**, **GROQ Cloud LLM APIs**, this demo shows how LLMs can assist climate modelers interactively.

---

## 🌍 Features

| Mode | Description |
|------|--------------|
| **Scenario Editor** | Upload an Excel input file (e.g. technology cost data). Give an instruction, and the agent writes and executes Pandas code to modify the file safely, producing an updated version for download. |
| **Document Q&A (RAG)** | Ask questions about your documentation (e.g. “what are the technologies in inv_cost sheet?”). Uses a simple docx/xlsx → chunks → embeddings → FAISS index → retriever → Gemini generator setup. |
| **MESSAGEix Executor Agent** | Upload a scenario file. Give instructions to run the model, and the agent solves the model and returns the objective value and solved model file for download. |

---

## 🧩 Folder Structure

```
project/
│
├── app.py
│
├── backend/
│   ├── config/
|   |    └── rag_config.py
│   ├── analysis_core/
│   |   ├── analysis_generator.py
│   |   └── analysis_plots.py
│   ├── rag_core/
│   |   ├── retriever.py
│   |   └── generator.py
|   |
|   ├── analysis_agent.py
|   ├── conv_history.py
|   ├── intent_detection.py
|   ├── orchestrator_agent.py
│   ├── rag_engine.py
|   ├── run_msg_model.py
│   └── scenario_editor.py
│
├── data/
│   ├── analysis_knowledgebase/
│   ├── docs/
|   └── history/
|      ├── conv_history.db
│      ├── outputs/
│      └── uploads/
|
├── doc_embedding/
│      ├── docx_parser.py
│      ├── xlsx_parser.py
│      └── index_manager.py
|
├── rag_store/
│      ├── faiss_hnsw_index.faiss
│      └── metadata_store.parquet
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<mariyamali4>/peach-messageix-chat-agent.git
   cd peach-messageix-chat-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv agent-env
   agent-env\Scripts\activate   # (Windows)
   # or
   source agent-env/bin/activate   # (Mac/Linux)
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your GROW Clous API key**
   You can either:
   - Add it to your environment variables:
     ```bash
     setx GROQ_API_KEY1 "your_api_key_here"
     ```
   - Or create a `.env` file in the root:
     ```
     GROQ_API_KEY1=your_api_key_here
     ```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

Then open the local URL displayed in the terminal:
```
http://localhost:8501
```

---

## 🧠 Example Use

**Scenario Editor**
> “Reduce investment cost by 10% for all solar technologies after 2030.”

**RAG**
> “What is the boundary condition for bound_activity?”

---

## 📦 Dependencies
> requirements.txt

---

## ⚠️ Safety

The code execution is sandboxed — unsafe operations (`os`, `sys`, `shutil`, etc.) are blocked.  
Only `numpy` and `pandas` imports are whitelisted.

---

## 💡 Future Work

- Analysis Agent: Interpretation of model output
- Automated evaluation pipeline

---
