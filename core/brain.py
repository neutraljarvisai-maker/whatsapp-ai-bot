import os
import logging
from typing import List, Dict, Any, Optional
from core.intelligence.factory import intelligence
from core.personality import PERSONALITY
from services.memory import memory_service
from core.vision.factory import vision_provider

logger = logging.getLogger(__name__)

class JarvisBrain:
    def __init__(self):
        self.intelligence = intelligence
        self.vision = vision_provider

    def process_user_message(self, system_instruction: str, user_message: str, context: str, history: List[Dict[str, str]] = None, user_id: str = "default_user") -> Dict[str, Any]:
        """Unified single-call architecture for VECTA processing with semantic memory."""

        # 1. Retrieve relevant memories
        memories = memory_service.search(user_id, user_message)
        memory_context = ""
        if memories:
            memory_context = "\nRELEVANT MEMORIES:\n" + "\n".join([f"- {m}" for m in memories])

        # 2. Augment context
        augmented_context = f"{context}{memory_context}"

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
        result = self.intelligence.generate_response(full_instruction, user_message, augmented_context, history)

        # 3. Store new facts into semantic memory if any were extracted
        facts = result.get("facts", {})
        if facts:
            for field, value in facts.items():
                fact_str = f"{field}: {value}"
                memory_service.store(user_id, fact_str, {"type": "profile_fact", "field": field})

        return result

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        """Vision-based task planning using the vision provider."""
        return self.vision.analyze_image(screenshot_path, task, history)

# Singleton instance for backward compatibility
brain = JarvisBrain()
