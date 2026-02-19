from llm_agents.base import AgentResult, BaseAgent


class DocumentationAgent(BaseAgent):
    name = "documentation"

    def handle(self, message: str) -> AgentResult:
        deliverables = [
            "Draft M&V plan sections from structured project data.",
            "Generate risk matrix and roles/responsibilities summary.",
            "Produce final savings narrative and report-ready language.",
        ]
        return AgentResult(
            engine=self.name,
            intent="implementation_or_reporting",
            response=f"Documentation output for: '{message}'\n- " + "\n- ".join(deliverables),
        )
