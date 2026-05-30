import pyautogui
import time
import os
import requests
import base64
from PIL import ImageGrab
import json
import re

# Configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

config = load_config()
BACKEND_URL = os.environ.get("JARVIS_BACKEND_URL", config.get("JARVIS_BACKEND_URL", "http://localhost:5000"))
USER_ID = os.environ.get("JARVIS_USER_ID", config.get("JARVIS_USER_ID", "default_user"))

class ActionExecutor:
    def __init__(self):
        pyautogui.FAILSAFE = True # Move mouse to corner to abort

    def take_screenshot(self, filename="screenshot.png"):
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        return filename

    def execute_action(self, action_str):
        """Parses and executes an action string like CLICK(100, 200)."""
        print(f"Executing action: {action_str}")
        try:
            if action_str.startswith("CLICK"):
                coords = re.findall(r'\d+', action_str)
                pyautogui.click(int(coords[0]), int(coords[1]))
            elif action_str.startswith("DOUBLE_CLICK"):
                coords = re.findall(r'\d+', action_str)
                pyautogui.doubleClick(int(coords[0]), int(coords[1]))
            elif action_str.startswith("RIGHT_CLICK"):
                coords = re.findall(r'\d+', action_str)
                pyautogui.rightClick(int(coords[0]), int(coords[1]))
            elif action_str.startswith("TYPE"):
                text = re.search(r'["\'](.*?)["\']', action_str).group(1)
                pyautogui.write(text)
            elif action_str.startswith("PRESS"):
                key = re.search(r'["\'](.*?)["\']', action_str).group(1)
                pyautogui.press(key)
            elif action_str.startswith("DRAG"):
                coords = re.findall(r'\d+', action_str)
                pyautogui.dragTo(int(coords[2]), int(coords[3]), duration=1.0)
            elif action_str.startswith("WAIT"):
                seconds = int(re.findall(r'\d+', action_str)[0])
                time.sleep(seconds)
            return True
        except Exception as e:
            print(f"Error executing action: {e}")
            return False

    def run_task(self, task):
        """Thinking loop that interacts with the backend."""
        history = []
        while True:
            screenshot_path = self.take_screenshot()

            with open(screenshot_path, 'rb') as f:
                files = {'screenshot': f}
                data = {
                    'task': task,
                    'user_id': USER_ID,
                    'history': "|".join(history[-5:]) # Last 5 actions
                }
                response = requests.post(f"{BACKEND_URL}/api/v1/plan_action", files=files, data=data)

            if response.status_code != 200:
                print("Backend error planning action.")
                break

            result = response.json().get("action", {})
            thought = result.get("thought", "Analyzing...")
            action = result.get("action", "DONE")

            print(f"VECTA THOUGHT: {thought}")
            print(f"VECTA ACTION: {action}")

            if action == "DONE" or action.startswith("FAIL"):
                print(f"Task finished: {action}")
                break

            if self.execute_action(action):
                history.append(action)
            else:
                print("Action execution failed.")
                break

            time.sleep(1) # Small delay between actions

if __name__ == "__main__":
    import sys
    task = sys.argv[1] if len(sys.argv) > 1 else "Complete pending tasks"
    executor = ActionExecutor()
    executor.run_task(task)
