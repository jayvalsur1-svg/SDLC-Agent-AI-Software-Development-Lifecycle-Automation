# 🚀 Autonomous SDLC Multi-Agent Pipeline

An end-to-end, autonomous **Software Development Life Cycle (SDLC)** agent pipeline built with **LangGraph**, **LangChain**, **Groq**, **OpenAI**, and **Tavily**. 

The system takes a high-level natural language prompt (e.g., *"Build a full-stack Task Manager web app with FastAPI and HTML/JS"*), researches technical stack recommendations, architects full project file structures, recursively implements production-ready source code, and runs automated QA testing with self-healing code repair routines inside a sandboxed environment.

---

## 🌟 Architecture & Workflow Overview

The system operates as a stateful, looping directed graph managed by **LangGraph**:

```
                       ┌─────────────────────────┐
                       │       START State       │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │     Planning_phase      │ 💡 Distills prompt into MVP app concept
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │     Analysis_phase      │ 🔍 Extracts requirements & searches Tavily
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │     Designing_phase     │ 📐 Architectures tech stack & file tree
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐◄──────┐
                       │  Implementation_phase   │       │ (Iterates file by file)
                       └────────────┬────────────┘───────┘
                                    │ (When all files written: status == "DONE")
                                    ▼
                       ┌─────────────────────────┐◄──────┐
                       │      Testing_phase      │       │ (Retries up to 3 times on test failure)
                       └────────────┬────────────┘───────┘
                                    │ (status in ["Test_passed", "Failed_max_retries"])
                                    ▼
                       ┌─────────────────────────┐
                       │        END State        │
                       └─────────────────────────┘
```

---

## 🧩 Pipeline Stages

1. **Planning Phase (`qwen3.8-27b`)**
   - Distills raw, ambiguous user prompts into clear MVP project concepts and target value propositions.
2. **Analysis & Research Phase (`qwen3.8-27b` + Tavily)**
   - Formulates precise functional requirements and executes high-signal web search queries via Tavily to fetch relevant library references and modern architectural patterns.
3. **Designing Phase (`openai/gpt-oss-120b`)**
   - Architectures the full application structure, selecting tech stacks, defining core features, and outlining precise relative file paths and descriptions.
4. **Implementation Phase (`gpt-6-luna` ReAct Agent)**
   - Iterates sequentially through the planned file tree. For each file, a tool-using ReAct agent writes modular code to disk using custom file tools (`read_file`, `write_file`, `list_files`, `get_current_directory`).
5. **Testing & QA Phase (`gpt-6-luna` ReAct Agent + Subprocess Sandbox)**
   - Installs dependencies (`pip`, `npm`), constructs unit and functional tests (`pytest`), and executes non-blocking command-line verification via `run_command`.
   - If tests fail, the QA agent inspects the error tracebacks, edits source files on disk, and re-executes tests until verification passes (up to 3 retry attempts).

---

## 🛠️ Tooling & Safety Features

* **Path Sandboxing (`safe_path_for_project`)**: Ensures all read/write file operations are restricted within the `./generated_project` directory to prevent unauthorized filesystem access.
* **Command Guardrails (`run_command`)**: Blocks unsafe shell execution commands (e.g., `rm -rf`, `sudo`, `shutdown`) and enforces a 60-second execution timeout.
* **LangSmith Observability**: Configured with full trace capturing for monitoring multi-agent step transitions and token usage.

---

## ⚙️ Setup & Installation

### 1. Prerequisites

- **Python 3.10+**
- Active API keys for **Groq**, **OpenAI**, **Tavily**, and **LangSmith**.

### 2. Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
groq1=your_groq_api_key_1
groq2=your_groq_api_key_2
TAVILY_API_KEY=your_tavily_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=SDLC-Agent-Analysis
```

### 3. Dependencies Installation

```bash
pip install langgraph langchain-groq langchain-openai langchain-core tavily-python pydantic python-dotenv
```

---

## 🚀 Execution

Run the main pipeline to generate and test an application inside the `./generated_project` directory:

```bash
python main.py
```

### Initial State Example

```python
initial_state = {
    "user_prompt": "Build a full-stack Task Manager web app with FastAPI and HTML/JS",
    "current_step_idx": 0,
    "completed_files": [],
    "test_attempts": 0,
    "status": "STARTED"
}
```

---

## 📊 Outputs & Artifacts

- **`./generated_project/`**: Folder containing the complete source code, configuration files (`requirements.txt`), and tests written by the agents.
- **LangSmith Tracing**: Full execution step inspection, tool invocation logs, and state history accessible in your LangSmith dashboard under project `SDLC-Agent-Analysis`.

---

## 📜 License

MIT License. Free for open-source modification and deployment.
