from __future__ import annotations

from collections import Counter
from typing import Any


REQUIRED_VOLUNTEER_FIELDS = {"program_id", "school_name", "major_name", "evidence_id", "source_file"}


def audit_plan_rows(rows: list[dict[str, Any]], strategy_result: dict[str, Any] | None = None) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    statuses = Counter()
    for idx, row in enumerate(rows, start=1):
        missing = sorted(field for field in REQUIRED_VOLUNTEER_FIELDS if not row.get(field))
        subject_status = str(row.get("subject_check_status", "REVIEW")).upper()
        region_status = str(row.get("region_check_status", row.get("region_status", "REVIEW"))).upper()
        statuses[subject_status] += 1
        if missing:
            failures.append({"row": idx, "reason_code": "MISSING_REQUIRED_FIELDS", "fields": missing})
        if subject_status != "PASS":
            failures.append({"row": idx, "reason_code": "SUBJECT_NOT_PASS", "status": subject_status})
        if region_status in {"BLOCK", "REVIEW"}:
            failures.append({"row": idx, "reason_code": "REGION_NOT_RESOLVED", "status": region_status})

    if strategy_result and not strategy_result.get("hard_gate_passed"):
        failures.append({"row": None, "reason_code": "STRATEGY_HARD_GATE_FAILED", "violations": strategy_result.get("violations", [])})

    if len(rows) != 96:
        failures.append({"row": None, "reason_code": "VOLUNTEER_COUNT_NOT_96", "count": len(rows)})

    violations = [failure["reason_code"] for failure in failures]
    hard_gate_passed = not failures
    return {
        "hard_gate_passed": hard_gate_passed,
        "total_rows": len(rows),
        "summary": dict(statuses),
        "failures": failures,
        "violations": violations,
        "formal_delivery_allowed": hard_gate_passed,
    }
