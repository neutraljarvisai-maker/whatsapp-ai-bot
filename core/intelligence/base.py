from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseIntelligence(ABC):
    @abstractmethod
    def generate_response(self, system_instruction: str, user_message: str, context: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        pass
