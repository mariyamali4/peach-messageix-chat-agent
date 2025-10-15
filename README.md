# 🍑 Peach — Climate Scenario Chat Agent

**Peach** is a chat agents that lets users:
1. **Edit MESSAGEix-style scenario Excel files** using natural-language instructions.
2. **Query supporting documentation** (e.g. messaeg_ix documentation files, current policy documents) using a robust RAG system.

Built with **Streamlit**, **LangChain**, and **Google Gemini**, this demo shows how LLMs can assist climate modelers interactively.

---

## 🌍 Features

| Mode | Description |
|------|--------------|
| **Scenario Editor** | Upload an Excel input file (e.g. technology cost data). Give an instruction, and the agent writes and executes Pandas code to modify the file safely, producing an updated version for download. |
| **Document Q&A (RAG)** | Ask questions about your documentation (e.g. “what are the technologies in inv_cost sheet?”). Uses a simple docx/xlsx → chunk → embeddings → FAISS index → retriever → Gemini generator setup. |

---

## 🧩 Folder Structure

```
project/
│
├── app_chat.py
│
├── backend/
│   ├── rag_agent.py
│   ├── scenario_editor.py
│   ├── main_agent.py
│   │
│   ├── rag_backend/
│   │   ├── doc_embedding/
│   │   │   ├── docx_parser.py
│   │   │   ├── xlsx_parser.py
│   │   │   └── index_manager.py
│   │   │
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   │
│   │   └── rag_store/
│   │       ├── faiss_hnsw_index.faiss
│   │       └── rag_metadata.parquet
│
├── data/
│   ├── docs/
│   ├── outputs/
│   └── uploads/
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/peach-messageix-chat-agent.git
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

4. **Set your Google Gemini API key**
   You can either:
   - Add it to your environment variables:
     ```bash
     setx GEMINI_API_KEY "your_api_key_here"
     ```
   - Or create a `.env` file in the root:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

---

## ▶️ Running the App

```bash
streamlit run app_chat.py
```

Then open the local URL displayed in the terminal:
```
http://localhost:8501
```

---

## 🧠 Example Use

**Scenario Editor**
> “Reduce `inv_cost` by 10% for all solar technologies after 2030.”

**RAG**
> “What is the boundary condition for `bound_activity`?”

---

## 📦 Dependencies

- pandas
- numpy
- google-generativeai
- sentence-transformers
- python-docx
- docx2txt
- python-docx
- streamlit
- faiss-cpu

---

## ⚠️ Safety

The code execution is sandboxed — unsafe operations (`os`, `sys`, `shutil`, etc.) are blocked.  
Only `numpy` and `pandas` imports are whitelisted.

---

## 💡 Future Work

- Add authentication
- Integration with MESSAGEix solver backend
- Editable visualization for scenario deltas

---
