from typing import Any, Dict

from llm_agents.analytics_agent import AnalyticsAgent
from llm_agents.constraints import validate_output
from llm_agents.documentation_agent import DocumentationAgent
from llm_agents.guidance_agent import GuidanceAgent
from llm_agents.strategy_agent import StrategyAgent
from llm_agents.trace_logger import TraceLogger


class Orchestrator:
    def __init__(self, trace_dir: str = "data/traces") -> None:
        self.strategy = StrategyAgent()
        self.analytics = AnalyticsAgent()
        self.documentation = DocumentationAgent()
        self.guidance = GuidanceAgent(
            strategy=self.strategy,
            analytics=self.analytics,
            documentation=self.documentation,
        )
        self.tracer = TraceLogger(log_dir=trace_dir)

    def _route(self, message: str, context: Dict[str, Any]) -> str:
        """Routes the user's message to the appropriate agent based on intent."""
        if context.get("guided_mode"):
            return "guide"

        # Allow forcing an intent for testing or explicit control
        forced_intent = str(context.get("intent", "")).lower().strip()
        if forced_intent in {"strategy", "analytics", "documentation", "guide"}:
            return forced_intent

        # LLM-based intent classification
        # In a real-world scenario, this would be a call to an LLM API.
        # Here, we simulate the LLM's reasoning process.
        prompt = f"""
        Given the user's message, determine the primary intent.
        The available intents are: 'strategy', 'analytics', 'documentation'.

        - 'strategy': For planning, M&V options, or identifying variables.
        - 'analytics': For regression, QA/QC, savings calculations, or statistical analysis.
        - 'documentation': For generating reports, plans, or other documents.

        User Message: "{message}"

        Based on the message, the primary intent is:
        """

        # Simulate LLM response based on keywords for now, but this structure
        # allows for a future LLM-based implementation.
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
                "statistical",
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
                "generate",
            ]
        ):
            return "documentation"

        # Default to strategy for planning and general queries
        return "strategy"

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        trace = self.tracer.begin(message, context)
        intent = self._route(message, context)
        trace.chosen_route = intent

        if intent == "strategy":
            result = self.strategy.run(message, context)
            trace.agent_name = "strategy"
        elif intent == "analytics":
            result = self.analytics.run(message, context)
            trace.agent_name = "analytics"
        elif intent == "guide":
            result = self.guidance.run(message, context)
            trace.agent_name = "guide"
        else:
            result = self.documentation.run(message, context)
            trace.agent_name = "documentation"

        # --- constraint check ---
        constraint_target = result.get("stage_result", result)
        verdict = validate_output(constraint_target, context)
        if not verdict.passed:
            result["_constraint_blocked"] = True
            result["_constraint_violations"] = verdict.to_dict()["violations"]

        trace.agent_output = result
        trace.qa_outcome = verdict.to_dict()
        self.tracer.end(trace)

        return {
            "agent": trace.agent_name,
            "intent": intent,
            "result": result,
            "trace_id": trace.trace_id,
        }
