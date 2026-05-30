from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAgent(ABC):
    @abstractmethod
    def run(self, input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

class BaseTool(ABC):
    @property
    @abstractmethod
    def spec(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        pass

class BaseMemory(ABC):
    @abstractmethod
    def store(self, key: str, data: Any):
        pass

    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> List[Any]:
        pass
