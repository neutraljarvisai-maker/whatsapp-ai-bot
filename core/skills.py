import os
import json
import importlib.util
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class SkillRegistry:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skills = {}
        self.load_skills()

    def load_skills(self):
        """Dynamically load all Python skills from the skills directory."""
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            return

        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                skill_name = filename[:-3]
                file_path = os.path.join(self.skills_dir, filename)

                try:
                    spec = importlib.util.spec_from_file_location(skill_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    if hasattr(module, "SKILL_SPEC"):
                        self.skills[skill_name] = {
                            "spec": module.SKILL_SPEC,
                            "execute": module.execute
                        }
                        logger.info(f"Loaded skill: {skill_name}")
                except Exception as e:
                    logger.error(f"Error loading skill {skill_name}: {e}")

    def get_skill_descriptions(self) -> str:
        """Returns a string description of all available skills for the LLM."""
        descriptions = []
        for name, data in self.skills.items():
            spec = data["spec"]
            desc = f"- {name}: {spec.get('description', 'No description')}\n  Params: {json.dumps(spec.get('parameters', {}))}"
            descriptions.append(desc)
        return "\n".join(descriptions) if descriptions else "No specialized skills available."

    def execute_skill(self, skill_name: str, **kwargs) -> Any:
        """Executes a named skill."""
        if skill_name in self.skills:
            try:
                return self.skills[skill_name]["execute"](**kwargs)
            except Exception as e:
                return f"Error executing {skill_name}: {e}"
        return f"Skill {skill_name} not found."

# Singleton instance
registry = SkillRegistry()
