import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not set. Gemini functionality will be unavailable.")

class JarvisBrain:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.2, # Lower temperature for less hallucination
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 1024,
            }
        )

    def generate_response(self, system_instruction: str, user_prompt: str, history: List[Dict[str, str]] = None) -> str:
        """Generates a text response using Gemini 1.5 Flash."""
        try:
            # Gemini 1.5 Flash supports system_instruction directly in the constructor or via a specific method
            # For simplicity with start_chat, we can prepend it to the first message if history is empty
            # or use the system_instruction parameter in the GenerativeModel constructor if supported by the library version

            model_with_sys = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )

            chat = model_with_sys.start_chat(history=history or [])
            response = chat.send_message(user_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            return "I'm sorry, I encountered an error in my thinking module."

    def classify_intent(self, user_message: str, context: str) -> str:
        """Classifies user intent using Gemini for higher accuracy."""
        prompt = f"""Analyze the user's input and categorize their primary intent.
Respond ONLY with a single, uppercase label.

Available Intents:
- GREETING: Informal greetings.
- QUESTION: Factual info, explanations.
- ADD_EVENT: Create/schedule an event.
- CANCEL_EVENT: Delete/cancel an event.
- RECALL: Asking about existing schedule or saved profile data.
- TASK: A request to perform an action on the computer (e.g., "open chrome", "search for X", "type this", "tell me what's on the screen", "click the blue button"). If it requires seeing the screen or moving the mouse, it's a TASK.
- CHAT: General conversation, small talk.

Context:
{context}

User Message:
{user_message}

Label:"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().upper()
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "CHAT"

    def extract_facts(self, user_message: str, jarvis_reply: str, current_profile: str, available_fields: List[str]) -> Optional[Dict[str, str]]:
        """Extracts explicit facts from the conversation to update the profile."""
        prompt = f"""Extract EXPLICIT facts about the user from this interaction.
Available fields: {", ".join(available_fields)}

Current Profile Context:
{current_profile}

Interaction:
User: {user_message}
Jarvis: {jarvis_reply}

Rules:
1. ONLY extract explicit facts stated by the user.
2. Respond with a JSON object of field:value pairs.
3. If no new facts, respond with "{{}}".
4. Never guess or infer.

JSON Output:"""
        try:
            response = self.model.generate_content(prompt)
            # Find the JSON part in case there's extra text
            text = response.text.strip()
            if "{" in text and "}" in text:
                json_str = text[text.find("{"):text.rfind("}")+1]
                import json
                return json.loads(json_str)
            return None
        except Exception as e:
            logger.error(f"Error extracting facts: {e}")
            return None

    def extract_event_details(self, user_message: str, context: str) -> Optional[Dict[str, str]]:
        """Extracts event details (title and datetime) from a message."""
        prompt = f"""Extract event details for a calendar entry.
Context: {context}
Message: {user_message}

Respond with JSON: {{"title": "...", "datetime": "..."}}
If not an event, respond with {{}}.
JSON Output:"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if "{" in text and "}" in text:
                import json
                return json.loads(text[text.find("{"):text.rfind("}")+1])
            return None
        except Exception as e:
            logger.error(f"Error extracting event details: {e}")
            return None

    def analyze_screen_and_plan(self, screenshot_path: str, task: str, history: List[str]) -> str:
        """Vision-based task planning for desktop control."""
        try:
            sample_file = genai.upload_file(path=screenshot_path)

            prompt = f"""You are Bat-Jarvis. You have control over a Windows 11 PC.
Current Task: {task}
Previous Actions: {", ".join(history) if history else "None"}

Look at the screenshot and decide the NEXT action.
Available Actions:
- CLICK(x, y): Click at coordinates.
- TYPE("text"): Type text.
- PRESS("key"): Press a specific key (e.g., 'enter', 'tab', 'esc').
- SCROLL(amount): Scroll up (+) or down (-).
- WAIT(seconds): Wait for a bit.
- DONE: Task is complete.
- FAIL("reason"): Task cannot be completed.

Respond ONLY with the action. Be precise with coordinates.
Action:"""

            response = self.model.generate_content([prompt, sample_file])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in vision task planning: {e}")
            return "FAIL('Vision system error')"

# Singleton instance
brain = JarvisBrain()
