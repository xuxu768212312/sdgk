from __future__ import annotations

from typing import Any

from sdgk.audits.subject_audit import audit_rows
from sdgk.core.paths import ROOT
from sdgk.indexes.subject import DEFAULT_DB_PATH, PASS_STATUS, REVIEW_STATUS, check_eligibility, connect_index, read_json


def unique_sample(where_sql: str) -> dict[str, Any]:
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
    assert row is not None, f"no unique sample for: {where_sql}"
    return {key: row[key] for key in row.keys()}


def test_index_count() -> None:
    files = ["2024版本科", "2024版专科", "2027版本科", "2027版专科"]
    expected = sum(len(read_json(ROOT / f"processed/选科要求/{name}.json")) for name in files)
    with connect_index(DEFAULT_DB_PATH) as conn:
        actual = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
    assert actual == expected


def test_subject_pass_block_review() -> None:
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
    assert none_result["status"] == PASS_STATUS

    pass_result = check_eligibility(
        year=2026,
        level="本科",
        subjects="物理,化学,生物",
        school_code=two_row["school_code"],
        major_code=two_row["major_code"],
        db_path=DEFAULT_DB_PATH,
    )
    assert pass_result["status"] == PASS_STATUS

    block_result = check_eligibility(
        year=2026,
        level="本科",
        subjects="历史,政治,生物",
        school_code=two_row["school_code"],
        major_code=two_row["major_code"],
        db_path=DEFAULT_DB_PATH,
    )
    assert block_result["status"] == "BLOCK"

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
    assert review_result["status"] == REVIEW_STATUS


def test_subject_audit_hard_gate() -> None:
    none_row = unique_sample("r.edition = '2024' AND r.level = '本科' AND r.subject_requirement_type = 'none'")
    two_row = unique_sample(
        "r.edition = '2024' AND r.level = '本科' "
        "AND r.subject_requirement_type = 'two' AND r.subjects_list = '物理|化学'"
    )
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
    assert pass_report["hard_gate_passed"]

    review_report = audit_rows(
        rows=rows
        + [
            {
                "院校代码": "99999",
                "院校名称": "不存在的学校",
                "专业代码": "NO_SUCH_MAJOR",
                "专业名称": "不存在的专业",
            }
        ],
        year=2026,
        edition=None,
        level="本科",
        subjects="物理,化学,生物",
        db_path=DEFAULT_DB_PATH,
    )
    assert not review_report["hard_gate_passed"]
