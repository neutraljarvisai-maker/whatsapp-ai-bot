# VECTA Roadmap to Production

## Phase 1: Foundational Architecture (Immediate Priority)
Transform VECTA from a collection of scripts into a modular agentic system.

### 1.1 Model Abstraction Layer (Intelligence Primitive)
*   Define `BaseIntelligence` interface.
*   Implement `GeminiIntelligence` (Cloud fallback).
*   Implement `OllamaIntelligence` (Local primary).
*   Add configuration-based runtime switching (e.g., `JARVIS_LLM_PROVIDER=ollama`).
*   Support `qwen3:8b`.

### 1.2 Enhanced ReAct Loop & Agent Framework
*   Implement a formal `Agent` class with internal state.
*   Develop a ReAct reasoning loop:
    1.  **Thought:** Internal reasoning about current state.
    2.  **Action:** Tool selection from registry.
    3.  **Observation:** Capture result/screenshot.
    4.  **Reflection:** Evaluate if step was successful or needs correction.
*   Support multi-turn tasks with a "Reasoning Depth" limit.

### 1.3 Persistent Memory & Retrieval
*   Integrate a lightweight vector store (e.g., ChromaDB or pgvector) for semantic retrieval.
*   Implement tiered memory:
    *   **Working Memory:** Recent conversation context (current turn).
    *   **Short-term:** Recent chat history (PostgreSQL).
    *   **Long-term:** Archived summaries and facts (Vector DB).
*   Implement automatic session compression/summarization.

---

## Phase 2: Computer Use & Local AI (High Priority)
Enabling VECTA to operate autonomously on the local device.

### 2.1 Vision System Refinement
*   Refactor `ActionExecutor` to provide cleaner observations back to the brain.
*   Integrate OCR (e.g., Tesseract or a vision model) to map screen coordinates to UI elements.
*   Implement multi-monitor support for screenshot capture.

### 2.2 Browser Automation (Playwright)
*   Create a `BrowserTool` using Playwright.
*   Support persistent sessions, tab management, and form interaction.
*   Implement safeguards (e.g., "Ask for permission" before submitting forms).

### 2.3 Ollama Optimization
*   Fine-tune system prompts for `qwen3:8b` to handle tool calling and coordinates reliably.
*   Implement streaming support for lower perceived latency.

---

## Phase 3: Capability Expansion (Medium Priority)
Reaching feature parity with OpenJarvis.

### 3.1 MCP & Skill Registry
*   Implement an MCP client for connecting to external servers (Google Drive, Slack, etc.).
*   Develop a `SkillRegistry` for hot-loading Python-based tools.
*   Implement skill metadata and versioning.

### 3.2 Background Scheduler
*   Develop a persistent job queue in PostgreSQL.
*   Implement a background worker for recurring tasks (Morning Briefing, System Monitoring).
*   Add retry logic and job history tracking.

---

## Phase 4: Production Readiness & UI Polish
Final stabilization for daily use.

### 4.1 Security & Reliability
*   Implement input sanitization and command allow-listing.
*   Add rate limiting and authentication to the backend.
*   Implement comprehensive error handling and logging (Sentry/ELK).

### 4.2 Frontend Sync & Performance
*   Optimize Three.js particle core for target 60 FPS.
*   Implement real-time state synchronization via WebSockets/SSE.
*   Enhance voice UI with lower latency TTS/STT.

---

## OpenJarvis Parity Roadmap
1.  **Architecture:** Adopt OpenJarvis's 5-primitive design (Intelligence, Engine, Agents, Tools/Memory, Learning).
2.  **Compatibility:** Support OpenJarvis tool standard (agentskills.io).
3.  **Local-First:** Shift all default processing to Ollama, using Gemini only as a high-tier fallback.
