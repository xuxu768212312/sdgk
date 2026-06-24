#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke tests for deterministic school-region lookup."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_school_region_index import build_index  # noqa: E402
from school_region import DEFAULT_REGION_DB_PATH, DEFAULT_REGION_META_PATH, check_school_regions, split_regions  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_index_build() -> None:
    meta = build_index(DEFAULT_REGION_DB_PATH, DEFAULT_REGION_META_PATH, rebuild=True)
    require(meta["row_count"] > 2500, "region index should include all unique schools from subject requirements")


def test_province_not_name_contains() -> None:
    for school in ("青岛大学", "济南大学", "烟台大学"):
        result = check_school_regions(split_regions("山东"), school_name=school)
        require(result["status"] == "MATCH", f"{school} should match 山东 by province")
        require(result["reason_code"] == "PROVINCE_MATCH", f"{school} should use province evidence")
        require(result["match_type"] == "province_exact", f"{school} must not rely on school-name text")

    result = check_school_regions(split_regions("山东"), school_name="北京大学")
    require(result["status"] == "NO_MATCH", "北京大学 should not match 山东")


def test_suzhou_city_overrides() -> None:
    for school in ("苏州大学", "西交利物浦大学", "常熟理工学院", "昆山杜克大学"):
        result = check_school_regions(split_regions("苏州"), school_name=school)
        require(result["status"] == "MATCH", f"{school} should match 苏州")
        require(result["matched_region"] == "苏州", f"{school} should expose matched 苏州")


def test_multi_city_review() -> None:
    result = check_school_regions(split_regions("青岛"), school_name="山东大学")
    require(result["status"] == "REVIEW", "山东大学 city-level query should require campus review")
    require(result["reason_code"] == "MULTI_CITY_REVIEW", "multi-campus city match must not be guessed")

    province_result = check_school_regions(split_regions("山东"), school_name="山东大学")
    require(province_result["status"] == "MATCH", "山东大学 should still match 山东 province")


def main() -> int:
    test_index_build()
    test_province_not_name_contains()
    test_suzhou_city_overrides()
    test_multi_city_review()
    print(
        json.dumps(
            {
                "status": "OK",
                "tested": [
                    "index_build",
                    "province_not_name_contains",
                    "suzhou_city_overrides",
                    "multi_city_review",
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
