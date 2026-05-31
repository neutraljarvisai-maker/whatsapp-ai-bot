from typing import List, Dict, Any, Optional
import logging
import json

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

        for step in range(max_steps):
            # 1. Thought & Action Selection
            react_prompt = self._build_react_prompt(task, current_context, history)
            # Use intelligence to generate the next thought and action
            response = self.intelligence.generate_response(
                system_instruction=self._get_agent_system_prompt(),
                user_message=f"Current Task: {task}",
                context=current_context,
                history=self._format_history_for_llm(history)
            )

            thought = response.get("thought", "Thinking about the next step.")
            action_call = response.get("action")

            if not action_call or action_call == "DONE":
                break

            # 2. Action Execution & Observation
            observation = self._execute_tool(action_call)

            # 3. Reflection
            # Ask the LLM to reflect on the result
            reflection_result = self.intelligence.generate_response(
                system_instruction="Analyze the observation and determine if the action was successful.",
                user_message=f"Action: {action_call}\nObservation: {observation}",
                context=f"Original Task: {task}"
            )
            reflection = reflection_result.get("response", "Action processed.")

            history.append({
                "step": step + 1,
                "thought": thought,
                "action": action_call,
                "observation": observation,
                "reflection": reflection
            })

            if "SUCCESS" in reflection.upper():
                # Update context with new information if needed
                current_context += f"\nObservation: {observation}"

        return history

    def _get_agent_system_prompt(self):
        return f"""You are the {self.name} agent.
        Respond in JSON with 'thought' and 'action' keys.
        Available tools: {list(self.tools.keys())}
        Use 'DONE' as action when finished."""

    def _build_react_prompt(self, task, context, history):
        return f"Task: {task}\nContext: {context}\nHistory: {json.dumps(history)}"

    def _format_history_for_llm(self, history):
        # Convert internal history to a list of messages if needed
        return []

    def _execute_tool(self, action_call: str) -> str:
        # Placeholder for tool execution logic
        # In a real implementation, this would parse 'CLICK(100, 200)' and call a function
        return f"Executed {action_call}. Observation pending."
