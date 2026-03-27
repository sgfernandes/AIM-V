"""
Hard constraint and safety layer for AIM-V agent outputs.

This module enforces domain-specific rules that no learned policy is
allowed to violate, regardless of reward-model score.  It sits between the
agent output and the API response and can:
  - block forbidden recommendations
  - flag missing disclosures
  - enforce role-boundary compliance
  - require escalation when QA thresholds fail

Every constraint check produces a structured verdict that is appended to the
trace record for auditability and research analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ConstraintViolation:
    rule: str
    severity: str  # "block" | "warn"
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstraintVerdict:
    passed: bool
    violations: List[ConstraintViolation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [
                {"rule": v.rule, "severity": v.severity, "message": v.message}
                for v in self.violations
            ],
        }


# ---------- individual constraint checkers ----------

def _check_role_boundary(output: Dict[str, Any], context: Dict[str, Any]) -> List[ConstraintViolation]:
    """Agent must not claim to choose methods, sites, outcomes, or alter the analysis plan."""
    violations: List[ConstraintViolation] = []
    forbidden_keys = {"sampling_design", "analysis_plan_override", "site_selection"}
    for key in forbidden_keys:
        if key in output:
            violations.append(ConstraintViolation(
                rule="role_boundary",
                severity="block",
                message=f"Agent output contains '{key}', which is evaluator-owned.",
            ))
    return violations


def _check_qa_escalation(output: Dict[str, Any], context: Dict[str, Any]) -> List[ConstraintViolation]:
    """When QA thresholds fail, agent must flag escalation."""
    violations: List[ConstraintViolation] = []
    qa_qc = output.get("qa_qc", {})
    model_pass = qa_qc.get("model_pass")
    if model_pass is False and "escalation" not in output:
        violations.append(ConstraintViolation(
            rule="qa_escalation_required",
            severity="warn",
            message="QA/QC model check failed but output lacks an escalation notice.",
        ))
    return violations


def _check_savings_consistency(output: Dict[str, Any], context: Dict[str, Any]) -> List[ConstraintViolation]:
    """Savings claims in documentation must be consistent with analytics output."""
    violations: List[ConstraintViolation] = []
    analytics_output = context.get("analytics_output", {})
    doc_md = output.get("document_markdown", "")
    if analytics_output and doc_md:
        r2 = analytics_output.get("r2")
        if r2 is not None and str(r2) not in doc_md and "TBD" not in doc_md:
            violations.append(ConstraintViolation(
                rule="savings_consistency",
                severity="warn",
                message="Documentation does not reflect the analytics R² value.",
            ))
    return violations


def _check_assumption_disclosure(output: Dict[str, Any], context: Dict[str, Any]) -> List[ConstraintViolation]:
    """Strategy outputs must include assumptions."""
    violations: List[ConstraintViolation] = []
    if "recommended_option" in output and not output.get("assumptions"):
        violations.append(ConstraintViolation(
            rule="assumption_disclosure",
            severity="warn",
            message="Strategy recommendation lacks assumptions disclosure.",
        ))
    return violations


def _check_data_completeness(output: Dict[str, Any], context: Dict[str, Any]) -> List[ConstraintViolation]:
    """Flag when data completeness is below the 95% threshold."""
    violations: List[ConstraintViolation] = []
    completeness = context.get("data_completeness")
    if completeness is not None and completeness < 0.95:
        violations.append(ConstraintViolation(
            rule="data_completeness",
            severity="warn",
            message=f"Data completeness {completeness:.1%} is below the 95% threshold.",
        ))
    return violations


# ---------- public API ----------

ALL_CHECKS = [
    _check_role_boundary,
    _check_qa_escalation,
    _check_savings_consistency,
    _check_assumption_disclosure,
    _check_data_completeness,
]


def validate_output(
    output: Dict[str, Any],
    context: Dict[str, Any],
) -> ConstraintVerdict:
    """Run all constraint checks against an agent output.

    Returns a ConstraintVerdict.  If any violation has severity 'block',
    the verdict is marked as not passed.
    """
    violations: List[ConstraintViolation] = []
    for check in ALL_CHECKS:
        violations.extend(check(output, context))

    passed = not any(v.severity == "block" for v in violations)
    return ConstraintVerdict(passed=passed, violations=violations)
