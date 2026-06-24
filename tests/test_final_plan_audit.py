from __future__ import annotations

from sdgk.audits.final_plan_audit import audit_plan_rows


def row(index: int, subject: str = "PASS", region: str = "MATCH") -> dict:
    return {
        "program_id": f"p{index}",
        "school_name": f"学校{index}",
        "major_name": f"专业{index}",
        "evidence_id": f"e{index}",
        "source_file": "processed/投档表/test.json",
        "subject_check_status": subject,
        "region_check_status": region,
    }


def test_final_audit_blocks_review() -> None:
    rows = [row(i) for i in range(95)] + [row(96, subject="REVIEW")]
    result = audit_plan_rows(rows, strategy_result={"hard_gate_passed": True})
    assert not result["hard_gate_passed"]
    assert "SUBJECT_NOT_PASS" in result["violations"]


def test_final_audit_requires_96_rows() -> None:
    result = audit_plan_rows([row(1)], strategy_result={"hard_gate_passed": True})
    assert not result["hard_gate_passed"]
    assert "VOLUNTEER_COUNT_NOT_96" in result["violations"]


def test_final_audit_passes_clean_96() -> None:
    result = audit_plan_rows([row(i) for i in range(96)], strategy_result={"hard_gate_passed": True})
    assert result["hard_gate_passed"]
    assert result["formal_delivery_allowed"]
