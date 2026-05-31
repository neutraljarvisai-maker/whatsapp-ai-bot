from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVision(ABC):
    @abstractmethod
    def analyze_image(self, image_path: str, task: str, history: List[str] = None) -> str:
        """Analyzes an image and returns a recommended action or description."""
        pass
