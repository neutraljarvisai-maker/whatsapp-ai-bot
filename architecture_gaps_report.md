# VECTA Architecture Gaps Report

## 1. Memory System Gaps
- **Semantic Search**: Current memory is SQL-based (exact match or linear scan). Missing vector embedding integration (e.g., ChromaDB or pgvector).
- **Memory Compression**: Automated summarization of old conversation turns is planned but not yet implemented.
- **Tiered Retrieval**: Missing a clear distinction and specialized retrieval for Short-term vs. Long-term memory.

## 2. ReAct Reasoning Gaps
- **Tool Integration**: While the ReAct loop exists in `BaseAgent`, it is not yet wired to a comprehensive set of real-world tools.
- **Dynamic Replanning**: The loop is currently linear. Missing the ability to branch or backtrack based on complex observations.
- **Reflection Quality**: The reflection step depends heavily on LLM quality; currently lacks a deterministic verification layer for critical actions.

## 3. Computer Use & Automation Gaps
- **Multimodal Local Support**: `analyze_screen_and_plan` lacks a local provider. Needs integration with models like `llava` or `moondream`.
- **Browser Automation**: Playwright integration is planned but missing. VECTA cannot currently interact with web applications beyond simple screenshot analysis.
- **OCR Integration**: Relies on LLM vision for coordinate detection. Missing local OCR (e.g., Tesseract) for precise UI element mapping.

## 4. OpenJarvis Parity Gaps
- **MCP Client**: Missing support for Model Context Protocol to connect to external data sources and tools.
- **Skill Registry**: No formal system for hot-loading, versioning, or managing permissions for new skills.
- **Background Scheduler**: No persistent task queue or background worker for autonomous actions (e.g., Morning Briefing).
- **Learning Primitive**: Missing the ability to improve model behavior or prompts based on interaction traces.

## 5. Technical Debt
- **WhatsApp Refactoring**: `whatsapp_ai.py` remains a legacy island and needs to be unified with the `core/intelligence` factory.
- **Error Propagation**: Need a unified error handling strategy across the frontend-backend-intelligence bridge.
- **Frontend State**: Synchronization between the backend and the Electron UI is currently basic and could benefit from WebSockets for real-time updates.
