import google.generativeai as genai
import os
import logging
from typing import List
from core.vision.base import BaseVision

logger = logging.getLogger(__name__)

class GeminiVision(BaseVision):
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.warning("GEMINI_API_KEY not set for GeminiVision.")

        self.model = genai.GenerativeModel(model_name=model_name)

    def analyze_image(self, image_path: str, task: str, history: List[str] = None) -> str:
        try:
            sample_file = genai.upload_file(path=image_path)

            history_text = "\n".join(history) if history else "No previous actions."
            prompt = f"""You are VECTA, controlling a Windows PC.
Objective: {task}
History: {history_text}

Analyze the screen and return the NEXT action.
Example: CLICK(500, 300) or TYPE("hello") or DONE.
Action:"""

            response = self.model.generate_content([prompt, sample_file])
            return response.text.strip()
        except Exception as e:
            logger.error(f"GeminiVision error: {e}")
            return f"FAIL('Vision system error: {e}')"
