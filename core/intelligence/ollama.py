import requests
import logging
from typing import List, Dict, Any, Optional
from core.intelligence.base import BaseIntelligence

logger = logging.getLogger(__name__)

class OllamaIntelligence(BaseIntelligence):
    def __init__(self, model_name: str = "qwen3:8b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate_response(self, system_instruction: str, user_message: str, context: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        prompt = f"{system_instruction}\n\nContext:\n{context}\n\nUser: {user_message}\n\nRespond in JSON format."
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            response.raise_for_status()
            return response.json().get("response", {})
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"intent": "CHAT", "response": "Local intelligence unavailable.", "facts": {}, "event": {}}

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        # qwen3:8b might not support vision directly via Ollama generate API easily without multimodal model
        # Placeholder for multimodal local model
        return "FAIL('Local vision not implemented')"
