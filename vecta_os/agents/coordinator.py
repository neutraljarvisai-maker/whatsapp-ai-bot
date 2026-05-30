from vecta_os.core.interfaces import BaseAgent
from vecta_os.core.brain import brain
from vecta_os.core.registry import registry
from vecta_os.personality.base import VECTA_SYSTEM_PROMPT
from typing import Dict, Any, Optional

class CoordinatorAgent(BaseAgent):
    """Orchestrator for VECTA CLOUD OS."""
    def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        skills = registry.list_specs()

        # Prepare context-rich instruction
        instruction = f"""{VECTA_SYSTEM_PROMPT}

        AVAILABLE SKILLS:
        {skills}

        CURRENT CONTEXT:
        {context}
        """

        # Execute unified reasoning
        result = brain.ask(instruction, user_input)

        # Action Loop (ReAct style)
        if "action" in result and result["action"] != "DONE":
            # Logic to execute skills or delegate to sub-agents would go here
            pass

        return result

coordinator = CoordinatorAgent()
