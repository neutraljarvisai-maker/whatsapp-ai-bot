import google.generativeai as genai
from typing import List, Dict, Any, Optional
import json
import logging
from vecta_os.core.config import config
from vecta_os.core.registry import registry as skill_registry
from vecta_os.mcp.hub import mcp_hub

logger = logging.getLogger(__name__)

if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)

class BrainService:
    """Core reasoning engine for VECTA CLOUD OS."""
    def __init__(self, model_name: str = config.DEFAULT_MODEL):
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"temperature": 0.1, "max_output_tokens": 4096}
        )

    def ask(self, system_instruction: str, user_input: str, history: List[Dict] = None) -> Dict[str, Any]:
        """Unified structured request for all VECTA interactions."""
        skills_desc = skill_registry.list_specs()
        mcp_tools = mcp_hub.list_tools()
        mcp_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in mcp_tools])

        full_system_prompt = f"""{system_instruction}

AVAILABLE SKILLS (Local Python functions):
{skills_desc}

MCP TOOLS (External Data Connections):
{mcp_desc}

TASK:
Analyze the user's message and current context. Perform intent classification, response generation, and data extraction in one step.

AVAILABLE INTENTS:
- GREETING: Informal greetings.
- QUESTION: Factual info, explanations.
- ADD_EVENT: Create/schedule an event.
- CANCEL_EVENT: Delete/cancel an event.
- RECALL: Asking about schedule or profile data.
- TASK: System control request (e.g., "open chrome", "click X").
- CHAT: General conversation.

EXTRACTION RULES:
- "facts": Extract explicit user profile facts (e.g., "my name is Bruce").
- "event": If ADD_EVENT, extract {{"title": "...", "datetime": "..."}}.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object. No other text.
{{
  "intent": "GREETING | QUESTION | ADD_EVENT | CANCEL_EVENT | RECALL | TASK | CHAT",
  "thought": "Your internal reasoning process as VECTA",
  "response": "Your spoken/text response to the user",
  "action": "OPTIONAL: CLICK(x, y) | TYPE('text') | PRESS('key') | DRAG(x1, y1, x2, y2) | WAIT(sec) | DONE | FAIL('reason')",
  "facts": {{}},
  "event": {{}}
}}
"""
        model_with_sys = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=full_system_prompt
        )
        try:
            chat = model_with_sys.start_chat(history=history or [])
            response = chat.send_message(user_input)
            text = response.text.strip()

            # JSON extraction logic
            if "{" in text and "}" in text:
                json_str = text[text.find("{"):text.rfind("}")+1]
                return json.loads(json_str)
            return {"response": text, "intent": "CHAT"}
        except Exception as e:
            logger.error(f"Brain execution error: {e}")
            return {"error": str(e), "response": "I encountered a core logic disturbance."}

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> Dict[str, Any]:
        """Vision-based ReAct planning loop for desktop control."""
        try:
            sample_file = genai.upload_file(path=screenshot_path)

            prompt = f"""You are VECTA, a superior autonomous AI entity. You are performing a ReAct loop to complete this objective: '{task}'.

HISTORY OF ACTIONS:
{chr(10).join(history) if history else "Initial state."}

CAPABILITIES:
- CLICK(x, y)
- DOUBLE_CLICK(x, y)
- RIGHT_CLICK(x, y)
- TYPE("text")
- PRESS("key")
- DRAG(x1, y1, x2, y2)
- WAIT(seconds)
- DONE
- FAIL("reason")

INSTRUCTIONS:
1. Observe the current screen state.
2. Formulate a 'thought' about what to do next based on your observation and history.
3. Choose an 'action' from the list above.
4. Output your response as JSON.

OUTPUT FORMAT:
{{
  "thought": "Your reasoning here",
  "action": "ACTION_CALL"
}}

Action:"""

            response = self.model.generate_content([prompt, sample_file])
            text = response.text.strip()
            import json
            if "{" in text and "}" in text:
                return json.loads(text[text.find("{"):text.rfind("}")+1])
            return {"thought": "Parsing error", "action": "FAIL('JSON parsing error')"}
        except Exception as e:
            logger.error(f"Error in vision task planning: {e}")
            return {"thought": "Vision error", "action": "FAIL('Vision system error')"}

brain = BrainService()
