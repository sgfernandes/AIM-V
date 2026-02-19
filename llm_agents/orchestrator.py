from llm_agents.analytics_agent import AnalyticsAgent
from llm_agents.base import AgentResult
from llm_agents.documentation_agent import DocumentationAgent
from llm_agents.strategy_agent import StrategyAgent


class Orchestrator:
    def __init__(self) -> None:
        self.strategy = StrategyAgent()
        self.analytics = AnalyticsAgent()
        self.documentation = DocumentationAgent()

    def route(self, message: str) -> AgentResult:
        text = message.lower()

        if self._is_strategy_request(text):
            return self.strategy.handle(message)
        if self._is_analytics_request(text):
            return self.analytics.handle(message)
        if self._is_documentation_request(text):
            return self.documentation.handle(message)
        return self.strategy.handle(message)

    @staticmethod
    def _is_strategy_request(text: str) -> bool:
        keywords = [
            "strategy",
            "planning",
            "m&v option",
            "boundary",
            "independent variable",
            "measurement boundary",
            "facility type",
        ]
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _is_analytics_request(text: str) -> bool:
        keywords = [
            "baseline",
            "regression",
            "r2",
            "cv(rmse)",
            "qaqc",
            "qa/qc",
            "post-implementation",
            "savings calculation",
        ]
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _is_documentation_request(text: str) -> bool:
        keywords = [
            "report",
            "documentation",
            "template",
            "risk matrix",
            "responsibility",
            "write-up",
        ]
        return any(keyword in text for keyword in keywords)
