import os
import logging
from typing import List, Dict, Any, Optional
from core.intelligence.factory import intelligence
from core.personality import PERSONALITY

logger = logging.getLogger(__name__)

class JarvisBrain:
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        # Use the abstracted intelligence provider
        self.provider = intelligence

    def process_user_message(self, system_instruction: str, user_message: str, context: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Unified single-call architecture for VECTA processing."""
        full_instruction = f"""{system_instruction}

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
- "facts": Extract explicit user profile facts.
- "event": If ADD_EVENT, extract {{"title": "...", "datetime": "..."}}.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object. No other text.
{{
  "intent": "GREETING | QUESTION | ADD_EVENT | CANCEL_EVENT | RECALL | TASK | CHAT",
  "response": "Your spoken/text response as VECTA",
  "facts": {{}},
  "event": {{}}
}}"""
        return self.provider.generate_response(full_instruction, user_message, context, history)

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        """Vision-based task planning for desktop control."""
        return self.provider.analyze_screen_and_plan(screenshot_path, task, history)

# Singleton instance for backward compatibility
brain = JarvisBrain()
