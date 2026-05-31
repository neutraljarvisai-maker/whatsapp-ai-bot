import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
from core.intelligence.base import BaseIntelligence

logger = logging.getLogger(__name__)

class GeminiIntelligence(BaseIntelligence):
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.warning("GEMINI_API_KEY not set.")

        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 2048,
            }
        )

    def generate_response(self, system_instruction: str, user_message: str, context: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        full_system_prompt = f"""{system_instruction}

TASK:
Analyze the user's message and current context. Perform intent classification, response generation, and data extraction in one step.

AVAILABLE INTENTS:
- GREETING, QUESTION, ADD_EVENT, CANCEL_EVENT, RECALL, TASK, CHAT.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object.
{{
  "intent": "...",
  "response": "...",
  "facts": {{}},
  "event": {{}}
}}

CONTEXT:
{context}
"""
        try:
            model_with_sys = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=full_system_prompt
            )
            chat = model_with_sys.start_chat(history=history or [])
            response = chat.send_message(user_message)
            text = response.text.strip()

            import json
            if "{" in text and "}" in text:
                json_str = text[text.find("{"):text.rfind("}")+1]
                return json.loads(json_str)
            return {{"intent": "CHAT", "response": text, "facts": {{}}, "event": {{}}}}
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return {{"intent": "CHAT", "response": "Intelligence failure.", "facts": {{}}, "event": {{}}}}

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        try:
            sample_file = genai.upload_file(path=screenshot_path)
            prompt = f"Objective: {task}\nHistory: {'|'.join(history)}\nAction:"
            response = self.model.generate_content([prompt, sample_file])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Vision error: {e}")
            return "FAIL"
