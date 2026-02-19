from llm_agents.base import AgentResult, BaseAgent


class StrategyAgent(BaseAgent):
    name = "strategy"

    def handle(self, message: str) -> AgentResult:
        guidance = [
            "Classify load profile and operating schedule.",
            "Recommend an M&V option with boundary assumptions.",
            "List independent variables to collect for baseline modeling.",
        ]
        return AgentResult(
            engine=self.name,
            intent="planning",
            response=f"Strategy guidance for: '{message}'\n- " + "\n- ".join(guidance),
        )
