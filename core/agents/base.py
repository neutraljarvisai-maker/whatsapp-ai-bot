import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, name: str, intelligence, tools: Dict[str, Any] = None):
        self.name = name
        self.intelligence = intelligence
        self.tools = tools or {}
        self.memory = []

    def run_react_loop(self, task: str, context: str, max_steps: int = 5):
        """Formal ReAct loop: Thought -> Action -> Observation -> Reflection."""
        history = []
        current_context = context

        logger.info(f"Starting ReAct loop for task: {task}")

        for step in range(max_steps):
            # 1. Thought & Action Selection
            react_prompt = self._get_agent_system_prompt()
            user_msg = f"Task: {task}\nCurrent Context: {current_context}"

            logger.info(f"Step {step+1}: Thinking...")
            response = self.intelligence.generate_response(
                system_instruction=react_prompt,
                user_message=user_msg,
                context=json.dumps(history[-3:]) if history else "Start of task.",
                history=None
            )

            thought = response.get("thought", "Determining next step.")
            action_call = response.get("action")

            logger.info(f"Thought: {thought}")
            logger.info(f"Action: {action_call}")

            if not action_call or action_call == "DONE":
                logger.info("Task completed or no action specified.")
                break

            # 2. Action Execution & Observation
            observation = self._execute_tool(action_call)
            logger.info(f"Observation: {observation}")

            # 3. Reflection
            reflection_prompt = "You are a critical observer. Analyze the action and observation to determine success or next steps. Respond in JSON with a 'response' field."
            reflection_result = self.intelligence.generate_response(
                system_instruction=reflection_prompt,
                user_message=f"Action: {action_call}\nObservation: {observation}",
                context=f"Original Task: {task}"
            )
            reflection = reflection_result.get("response", "Action observed.")
            logger.info(f"Reflection: {reflection}")

            history.append({
                "step": step + 1,
                "thought": thought,
                "action": action_call,
                "observation": observation,
                "reflection": reflection
            })

            if "SUCCESS" in reflection.upper() and action_call != "DONE":
                current_context += f"\nResult: {observation}"

        return history

    def _get_agent_system_prompt(self):
        return f"""You are the {self.name} agent.
Respond ONLY with a valid JSON object containing 'thought' and 'action'.
Available tools: {list(self.tools.keys())}
Example: {{"thought": "I need to check the time.", "action": "GET_TIME()"}}
Use 'DONE' as action when finished."""

    def _execute_tool(self, action_call: str) -> str:
        """Parses and executes a tool call with arguments."""
        try:
            import re
            match = re.match(r"(\w+)\((.*)\)", action_call)
            if not match:
                return f"Error: Invalid action format {action_call}"

            tool_name, args_str = match.groups()
            if tool_name not in self.tools:
                return f"Error: Tool {tool_name} not found."

            # Simple argument parsing (comma-separated, stripped)
            args = [a.strip().strip("'\"") for a in args_str.split(",") if a.strip()]

            tool_func = self.tools[tool_name]
            import inspect
            if asyncio.iscoroutinefunction(tool_func):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(tool_func(*args))
            else:
                return tool_func(*args)

        except Exception as e:
            return f"Error executing tool: {e}"

import asyncio
