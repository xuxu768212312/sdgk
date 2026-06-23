#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check whether a student's subject combination can apply to one major."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

from subject_eligibility import BLOCK_STATUS, DEFAULT_DB_PATH, PASS_STATUS, REVIEW_STATUS, check_eligibility


def parse_year(value: Optional[str]) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return None
    return int(value)


def emit_human(result: dict[str, Any]) -> None:
    print(f"status: {result['status']}")
    print(f"eligible: {result['eligible']}")
    print(f"reason_code: {result['reason_code']}")
    print(f"match_type: {result['match_type']}")
    print(f"message: {result['message']}")
    print(f"evidence_id: {result.get('evidence_id') or ''}")
    print(f"source_file: {result.get('source_file') or ''}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically check subject eligibility.")
    parser.add_argument("--year", help="Admission year, e.g. 2026.")
    parser.add_argument("--edition", help="Subject requirement edition: 2024 or 2027.")
    parser.add_argument("--level", required=True, help="本科 or 专科.")
    parser.add_argument("--subjects", required=True, help="Three subjects, e.g. 物理,化学,生物.")
    parser.add_argument("--school-code", help="5-digit school code.")
    parser.add_argument("--major-code", help="Major code.")
    parser.add_argument("--school-name", help="School name fallback.")
    parser.add_argument("--major-name", help="Major name fallback.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite index path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    try:
        result = check_eligibility(
            year=parse_year(args.year),
            edition=args.edition,
            level=args.level,
            subjects=args.subjects,
            school_code=args.school_code,
            major_code=args.major_code,
            school_name=args.school_name,
            major_name=args.major_name,
            db_path=args.db,
        )
    except Exception as exc:
        result = {
            "status": REVIEW_STATUS,
            "eligible": None,
            "reason_code": "RUNTIME_ERROR",
            "match_type": "none",
            "message": str(exc),
            "evidence_id": None,
            "source_file": None,
            "evidence": None,
        }
        exit_code = 2
    else:
        exit_code = 0 if result["status"] == PASS_STATUS else 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        emit_human(result)

    if result["status"] not in {PASS_STATUS, BLOCK_STATUS, REVIEW_STATUS}:
        return 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
