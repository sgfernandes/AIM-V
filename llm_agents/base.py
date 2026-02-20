from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...
