from __future__ import annotations

from sdgk.indexes.region import DEFAULT_REGION_DB_PATH, check_school_regions, split_regions


def test_region_index_exists() -> None:
    assert DEFAULT_REGION_DB_PATH.exists()


def test_province_not_name_contains() -> None:
    for school in ("青岛大学", "济南大学", "烟台大学"):
        result = check_school_regions(split_regions("山东"), school_name=school)
        assert result["status"] == "MATCH"
        assert result["reason_code"] == "PROVINCE_MATCH"
        assert result["match_type"] == "province_exact"

    result = check_school_regions(split_regions("山东"), school_name="北京大学")
    assert result["status"] == "NO_MATCH"


def test_suzhou_city_overrides() -> None:
    for school in ("苏州大学", "西交利物浦大学", "常熟理工学院", "昆山杜克大学"):
        result = check_school_regions(split_regions("苏州"), school_name=school)
        assert result["status"] == "MATCH"
        assert result["matched_region"] == "苏州"


def test_suzhou_does_not_expand_to_jiangsu() -> None:
    result = check_school_regions(split_regions("苏州"), school_name="南京大学")
    assert result["status"] != "MATCH"


def test_multi_city_review() -> None:
    result = check_school_regions(split_regions("青岛"), school_name="山东大学")
    assert result["status"] == "REVIEW"
    assert result["reason_code"] == "MULTI_CITY_REVIEW"

    province_result = check_school_regions(split_regions("山东"), school_name="山东大学")
    assert province_result["status"] == "MATCH"
