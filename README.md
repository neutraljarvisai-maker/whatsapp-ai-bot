# VECTA: Cinematic AI Operating System

VECTA is a local-first, autonomous AI operating system inspired by the Batcomputer. It integrates desktop control, memory persistence, and modular intelligence providers.

## Core Features
- **Local-First Intelligence**: Support for Ollama and Qwen3:8b.
- **Vision-Guided Automation**: Control your desktop via natural language.
- **Memory Persistence**: Long-term profile and context storage via PostgreSQL.
- **Agentic Reasoning**: Multi-step task execution using ReAct loops.

## Setup Instructions

### 1. Prerequisites
- **Python 3.10+**
- **PostgreSQL**
- **Ollama** (for local-first operation)
- **Electron** (for the desktop UI)

### 2. Local AI Setup (Ollama)
1. Install [Ollama](https://ollama.com/).
2. Pull the default model:
   ```bash
   ollama pull qwen3:8b
   ```
3. Ensure the Ollama server is running (usually on port 11434).

### 3. Installation
```bash
# Clone the repository
git clone <repo-url>
cd vecta

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd client/ui
npm install
```

### 4. Configuration
Create a `.env` file based on `.env.example`:
```env
VECTA_LLM_PROVIDER=ollama
VECTA_OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=your_postgresql_url
```

### 5. Running VECTA
**Start the Backend:**
```bash
python desktop_backend.py
```

**Start the Desktop Client:**
```bash
cd client/ui
npm start
```

## Architecture
VECTA follows a modular primitive-based architecture:
- **Intelligence**: Abstraction layer for LLM providers (`core/intelligence`).
- **Agents**: ReAct-based task orchestrators (`core/agents`).
- **Services**: Database, Calendar, and Profile utilities (`services/`).
- **Client**: Electron UI and local system executor (`client/`).
