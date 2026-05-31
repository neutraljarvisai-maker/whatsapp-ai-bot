import json
import logging
import os
from typing import List, Dict, Any, Optional
from core.intelligence.base import BaseIntelligence

logger = logging.getLogger(__name__)

class OllamaIntelligence(BaseIntelligence):
    def __init__(self, model_name: str = "qwen3:8b", base_url: str = None):
        self.model_name = model_name
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        import requests
        self._requests = requests

    def generate_response(self, system_instruction: str, user_message: str, context: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        # Incorporate history into the prompt for stateful conversations
        history_text = ""
        if history:
            history_text = "RECENT HISTORY:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history]) + "\n\n"

        prompt = f"{system_instruction}\n\n{history_text}CONTEXT:\n{context}\n\nUSER MESSAGE: {user_message}\n\nRespond in JSON format."

        try:
            logger.info(f"Ollama ({self.model_name}) request to {self.base_url}")
            response = self._requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            response.raise_for_status()
            raw_response = response.json().get("response", "")

            if isinstance(raw_response, str):
                try:
                    return json.loads(raw_response)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from Ollama: {raw_response}")
                    return {"intent": "CHAT", "response": raw_response, "facts": {}, "event": {}}
            return raw_response

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"intent": "CHAT", "response": "Local intelligence (Ollama) is unavailable or timed out.", "facts": {}, "event": {}}

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        return f"FAIL('Ollama model {self.model_name} does not support vision/screenshots')"
