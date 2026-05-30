import os
import importlib.util
import logging
from typing import Dict, Any, List
from vecta_os.core.config import config

logger = logging.getLogger(__name__)

class SkillRegistry:
    """Industrial-grade Skill Registry inspired by OpenJarvis."""
    def __init__(self, skills_dir: str = config.SKILLS_DIR):
        self.skills_dir = skills_dir
        self.skills = {}
        self.load_all()

    def load_all(self):
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            return

        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                self.load_skill(filename[:-3])

    def load_skill(self, name: str):
        path = os.path.join(self.skills_dir, f"{name}.py")
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "SKILL_SPEC"):
                self.skills[name] = {
                    "spec": module.SKILL_SPEC,
                    "execute": module.execute,
                    "metadata": getattr(module, "METADATA", {})
                }
                logger.info(f"VECTA Skill Loaded: {name}")
        except Exception as e:
            logger.error(f"Failed to load skill {name}: {e}")

    def list_specs(self) -> List[Dict]:
        return [s["spec"] for s in self.skills.values()]

registry = SkillRegistry()
