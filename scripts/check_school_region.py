#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check whether a school belongs to requested province/city regions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from school_region import DEFAULT_REGION_DB_PATH, check_school_regions, split_regions


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically check school region match.")
    parser.add_argument("--regions", required=True, help="Comma/顿号 separated regions, e.g. 山东,苏州")
    parser.add_argument("--school-name", default="", help="School name.")
    parser.add_argument("--subject-school-code", default="", help="5-digit subject-index school code if available.")
    parser.add_argument("--db", type=Path, default=DEFAULT_REGION_DB_PATH)
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    args = parser.parse_args()

    try:
        regions = split_regions(args.regions)
        result = check_school_regions(
            regions=regions,
            school_name=args.school_name,
            subject_school_code=args.subject_school_code,
            db_path=args.db,
        )
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            json.dumps(
                {
                    "status": result.get("status"),
                    "matched": result.get("matched"),
                    "reason_code": result.get("reason_code"),
                    "match_type": result.get("match_type"),
                    "matched_region": result.get("matched_region"),
                    "province": result.get("province"),
                    "city": result.get("city"),
                    "evidence_id": result.get("evidence_id"),
                },
                ensure_ascii=False,
            )
        )
    if result.get("status") == "MATCH":
        return 0
    if result.get("status") in {"NO_MATCH", "REVIEW"}:
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
