from llm_agents.constraints import validate_output, ConstraintVerdict


def test_clean_output_passes():
    output = {
        "recommended_option": "IPMVP Option C",
        "assumptions": ["Baseline period representative."],
    }
    verdict = validate_output(output, {})
    assert verdict.passed is True
    assert len(verdict.violations) == 0


def test_role_boundary_violation_blocks():
    output = {"sampling_design": "random", "recommended_option": "C"}
    verdict = validate_output(output, {})
    assert verdict.passed is False
    rules = [v.rule for v in verdict.violations]
    assert "role_boundary" in rules


def test_qa_escalation_warning():
    output = {"qa_qc": {"model_pass": False}}
    verdict = validate_output(output, {})
    rules = [v.rule for v in verdict.violations]
    assert "qa_escalation_required" in rules
    # warnings don't block
    assert verdict.passed is True


def test_assumption_disclosure_warning():
    output = {"recommended_option": "IPMVP Option A"}
    verdict = validate_output(output, {})
    rules = [v.rule for v in verdict.violations]
    assert "assumption_disclosure" in rules


def test_data_completeness_warning():
    output = {}
    verdict = validate_output(output, {"data_completeness": 0.80})
    rules = [v.rule for v in verdict.violations]
    assert "data_completeness" in rules


def test_verdict_to_dict():
    output = {"qa_qc": {"model_pass": False}}
    verdict = validate_output(output, {})
    d = verdict.to_dict()
    assert "passed" in d
    assert "violations" in d
    assert isinstance(d["violations"], list)
