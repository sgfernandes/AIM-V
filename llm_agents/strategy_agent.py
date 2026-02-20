from typing import Any, Dict, List

from llm_agents.base import BaseAgent


class StrategyAgent(BaseAgent):
    name = "strategy"

    def _infer_option(self, c: Dict[str, Any]) -> str:
        retrofit_scope = str(c.get("retrofit_scope", "")).lower()
        measurement_isolation = bool(c.get("measurement_isolation", False))
        key_parameter_stable = bool(c.get("key_parameter_stable", False))
        whole_facility = bool(c.get("whole_facility", False))
        simulation_required = bool(c.get("simulation_required", False))

        if retrofit_scope in {"single_system", "single-system"} or measurement_isolation:
            return "IPMVP Option A" if key_parameter_stable else "IPMVP Option B"
        if whole_facility:
            return "IPMVP Option D" if simulation_required else "IPMVP Option C"
        return "IPMVP Option C"

    def _infer_independent_vars(self, message: str, c: Dict[str, Any]) -> List[str]:
        if c.get("independent_variables"):
            return list(c["independent_variables"])
        m = message.lower()
        vars_: List[str] = []
        if any(k in m for k in ["hvac", "cooling", "heating", "temperature"]):
            vars_.append("outdoor_temperature")
        if any(k in m for k in ["occupancy", "schedule", "hours"]):
            vars_.append("occupancy_or_operating_hours")
        if any(k in m for k in ["production", "throughput", "manufacturing"]):
            vars_.append("production_volume")
        return vars_ or ["outdoor_temperature", "operating_hours"]

    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        option = self._infer_option(context)
        indep_vars = self._infer_independent_vars(message, context)

        return {
            "recommended_option": option,
            "measurement_boundary": context.get(
                "measurement_boundary", "whole facility meter boundary"
            ),
            "independent_variables": indep_vars,
            "assumptions": [
                "Baseline period has representative operation.",
                "Meter and interval data quality are sufficient for modeling.",
            ],
            "next_actions": [
                "Confirm baseline period and exclusions.",
                "Collect interval/meter and driver data.",
                "Approve final M&V plan structure.",
            ],
        }
