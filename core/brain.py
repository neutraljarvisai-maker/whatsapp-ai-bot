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
        return self.provider.generate_response(system_instruction, user_message, context, history)

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        """Vision-based task planning for desktop control."""
        return self.provider.analyze_screen_and_plan(screenshot_path, task, history)

# Singleton instance for backward compatibility
brain = JarvisBrain()
