from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResult:
    engine: str
    intent: str
    response: str


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def handle(self, message: str) -> AgentResult:
        raise NotImplementedError
