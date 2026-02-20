from typing import Any, Dict

from llm_agents.base import BaseAgent


class DocumentationAgent(BaseAgent):
    name = "documentation"

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        project_name = context.get("project_name", "Untitled M&V Project")
        facility = context.get("facility", "Unknown Facility")
        strategy = context.get("strategy_output", {})
        analytics = context.get("analytics_output", {})

        option = strategy.get("recommended_option", "TBD")
        boundary = strategy.get("measurement_boundary", "TBD")
        indep_vars = strategy.get("independent_variables", [])
        r2 = analytics.get("r2", "TBD")
        cvrmse = analytics.get("cvrmse_percent", "TBD")
        qa = analytics.get("qa_qc", {}).get("pass", "TBD")

        doc_md = (
            f"# M&V Plan Summary\n\n"
            f"## Project\n"
            f"- **Project Name:** {project_name}\n"
            f"- **Facility:** {facility}\n\n"
            f"## Strategy\n"
            f"- **Recommended IPMVP Option:** {option}\n"
            f"- **Measurement Boundary:** {boundary}\n"
            f"- **Independent Variables:** {indep_vars}\n\n"
            f"## Analytics QA/QC\n"
            f"- **R\u00b2:** {r2}\n"
            f"- **CV(RMSE) %:** {cvrmse}\n"
            f"- **QA/QC Pass:** {qa}\n\n"
            f"## Reporting\n"
            f"- Baseline model and assumptions documented.\n"
            f"- Post-implementation savings to be verified against "
            f"approved boundary and exclusions.\n"
        )
        return {
            "document_type": "mv_plan_summary_markdown",
            "document_markdown": doc_md,
        }
