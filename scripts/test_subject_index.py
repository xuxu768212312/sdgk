#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke tests for the subject requirement index and hard gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from audit_volunteer_subjects import audit_rows
from subject_eligibility import DEFAULT_DB_PATH, PASS_STATUS, REVIEW_STATUS, check_eligibility, connect_index, read_json


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def unique_sample(where_sql: str) -> Dict[str, Any]:
    query = f"""
        SELECT *
        FROM requirements r
        WHERE {where_sql}
          AND (
            SELECT COUNT(*)
            FROM requirements x
            WHERE x.edition = r.edition
              AND x.level = r.level
              AND x.school_code = r.school_code
              AND x.major_code = r.major_code
          ) = 1
        ORDER BY row_id
        LIMIT 1
    """
    with connect_index(DEFAULT_DB_PATH) as conn:
        row = conn.execute(query).fetchone()
    require(row is not None, f"no unique sample for: {where_sql}")
    return {key: row[key] for key in row.keys()}


def test_index_count() -> None:
    files = ["2024版本科", "2024版专科", "2027版本科", "2027版专科"]
    expected = sum(len(read_json(ROOT / f"processed/选科要求/{name}.json")) for name in files)
    with connect_index(DEFAULT_DB_PATH) as conn:
        actual = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
    require(actual == expected, f"row count mismatch: expected {expected}, got {actual}")


def test_single_checks() -> tuple[Dict[str, Any], Dict[str, Any]]:
    none_row = unique_sample("r.edition = '2024' AND r.level = '本科' AND r.subject_requirement_type = 'none'")
    two_row = unique_sample(
        "r.edition = '2024' AND r.level = '本科' "
        "AND r.subject_requirement_type = 'two' AND r.subjects_list = '物理|化学'"
    )

    none_result = check_eligibility(
        year=2026,
        level="本科",
        subjects="历史,政治,生物",
        school_code=none_row["school_code"],
        major_code=none_row["major_code"],
        db_path=DEFAULT_DB_PATH,
    )
    require(none_result["status"] == PASS_STATUS, "none requirement should pass for any valid subjects")

    pass_result = check_eligibility(
        year=2026,
        level="本科",
        subjects="物理,化学,生物",
        school_code=two_row["school_code"],
        major_code=two_row["major_code"],
        db_path=DEFAULT_DB_PATH,
    )
    require(pass_result["status"] == PASS_STATUS, "物理+化学 requirement should pass when included")

    block_result = check_eligibility(
        year=2026,
        level="本科",
        subjects="历史,政治,生物",
        school_code=two_row["school_code"],
        major_code=two_row["major_code"],
        db_path=DEFAULT_DB_PATH,
    )
    require(block_result["status"] == "BLOCK", "物理+化学 requirement should block when missing")

    review_result = check_eligibility(
        year=2026,
        level="本科",
        subjects="物理,化学,生物",
        school_code="99999",
        major_code="NO_SUCH_MAJOR",
        school_name="不存在的学校",
        major_name="不存在的专业",
        db_path=DEFAULT_DB_PATH,
    )
    require(review_result["status"] == REVIEW_STATUS, "missing requirement row should return REVIEW")
    return none_row, two_row


def test_hard_gate(none_row: Dict[str, Any], two_row: Dict[str, Any]) -> None:
    rows = [
        {
            "院校代码": none_row["school_code"],
            "院校名称": none_row["school_name"],
            "专业代码": none_row["major_code"],
            "专业名称": none_row["major_name"],
        },
        {
            "院校代码": two_row["school_code"],
            "院校名称": two_row["school_name"],
            "专业代码": two_row["major_code"],
            "专业名称": two_row["major_name"],
        },
    ]
    pass_report = audit_rows(
        rows=rows,
        year=2026,
        edition=None,
        level="本科",
        subjects="物理,化学,生物",
        db_path=DEFAULT_DB_PATH,
    )
    require(pass_report["hard_gate_passed"], "all PASS rows should pass the hard gate")

    review_rows = rows + [
        {
            "院校代码": "99999",
            "院校名称": "不存在的学校",
            "专业代码": "NO_SUCH_MAJOR",
            "专业名称": "不存在的专业",
        }
    ]
    review_report = audit_rows(
        rows=review_rows,
        year=2026,
        edition=None,
        level="本科",
        subjects="物理,化学,生物",
        db_path=DEFAULT_DB_PATH,
    )
    require(not review_report["hard_gate_passed"], "REVIEW row should fail the hard gate")


def main() -> int:
    if not DEFAULT_DB_PATH.exists():
        print(json.dumps({"status": "ERROR", "message": "subject index is missing; run scripts/build_subject_index.py --rebuild"}, ensure_ascii=False))
        return 2
    test_index_count()
    none_row, two_row = test_single_checks()
    test_hard_gate(none_row, two_row)
    print(json.dumps({"status": "OK", "tested": ["index_count", "single_checks", "hard_gate"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
