from typing import Any, Dict

from llm_agents.analytics_agent import AnalyticsAgent
from llm_agents.documentation_agent import DocumentationAgent
from llm_agents.strategy_agent import StrategyAgent


class Orchestrator:
    def __init__(self) -> None:
        self.strategy = StrategyAgent()
        self.analytics = AnalyticsAgent()
        self.documentation = DocumentationAgent()

    def _route(self, message: str, context: Dict[str, Any]) -> str:
        forced = str(context.get("intent", "")).lower().strip()
        if forced in {"strategy", "analytics", "documentation"}:
            return forced

        m = message.lower()
        if any(
            k in m
            for k in [
                "regression",
                "r2",
                "cvrmse",
                "baseline",
                "savings",
                "qa",
                "qaqc",
                "analytics",
            ]
        ):
            return "analytics"
        if any(
            k in m
            for k in [
                "report",
                "document",
                "template",
                "write plan",
                "documentation",
            ]
        ):
            return "documentation"
        return "strategy"

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        intent = self._route(message, context)

        if intent == "strategy":
            result = self.strategy.run(message, context)
            return {"agent": "strategy", "intent": intent, "result": result}

        if intent == "analytics":
            result = self.analytics.run(message, context)
            return {"agent": "analytics", "intent": intent, "result": result}

        result = self.documentation.run(message, context)
        return {"agent": "documentation", "intent": intent, "result": result}
        return any(keyword in text for keyword in keywords)
