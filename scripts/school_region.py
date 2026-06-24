#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic school-region lookup utilities.

Province is sourced from official-derived subject requirement JSON files.
City is conservative: it is inferred from explicit school-name geography or a
small reviewed override table. Ambiguous multi-campus schools return REVIEW for
city-level matching instead of being guessed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
REGION_DIR = ROOT / "processed" / "院校地区"
DEFAULT_REGION_DB_PATH = REGION_DIR / "school_region_index.sqlite"
DEFAULT_REGION_META_PATH = REGION_DIR / "school_region_index_meta.json"

SUBJECT_SOURCE_FILES = [
    ROOT / "processed" / "选科要求" / "2024版本科.json",
    ROOT / "processed" / "选科要求" / "2024版专科.json",
    ROOT / "processed" / "选科要求" / "2027版本科.json",
    ROOT / "processed" / "选科要求" / "2027版专科.json",
]

PROVINCES = {
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "西藏",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
    "香港",
    "澳门",
    "台湾",
}

REGION_GROUPS = {
    "江浙沪": ["江苏", "浙江", "上海"],
    "长三角": ["江苏", "浙江", "上海", "安徽"],
    "山东省内": ["山东"],
    "省内": ["山东"],
    "江苏省内": ["江苏"],
}

# County-level aliases that users often treat as a city preference.
CITY_ALIAS_TO_CITY = {
    "常熟": "苏州",
    "昆山": "苏州",
    "太仓": "苏州",
    "张家港": "苏州",
    "吴江": "苏州",
}

CITY_OVERRIDES = {
    "西交利物浦大学": {"city": "苏州", "aliases": ["苏州"]},
    "常熟理工学院": {"city": "苏州", "aliases": ["常熟", "苏州"]},
    "昆山杜克大学": {"city": "苏州", "aliases": ["昆山", "苏州"]},
    "中国海洋大学": {"city": "青岛", "aliases": ["青岛"]},
    "中国石油大学(华东)": {"city": "青岛", "aliases": ["青岛"]},
    "哈尔滨工业大学(威海)": {"city": "威海", "aliases": ["威海"]},
    "山东大学威海分校": {"city": "威海", "aliases": ["威海"]},
}

MULTI_CITY_REVIEW = {
    "山东大学": ["济南", "青岛", "威海"],
    "山东科技大学": ["青岛", "济南", "泰安"],
    "山东第一医科大学": ["济南", "泰安"],
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_text(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .replace("（", "(")
        .replace("）", ")")
        .replace("　", "")
        .replace(" ", "")
    )


def normalize_region(value: str) -> str:
    region = normalize_text(value)
    for suffix in ("省", "市", "自治区", "壮族自治区", "回族自治区", "维吾尔自治区", "特别行政区"):
        if region.endswith(suffix):
            region = region[: -len(suffix)]
    return region


def split_regions(value: str) -> List[str]:
    parts = re.split(r"[,，、/;；\s]+", value or "")
    regions: List[str] = []
    for part in parts:
        normalized = normalize_region(part)
        if not normalized:
            continue
        regions.extend(REGION_GROUPS.get(normalized, [normalized]))
    return regions


def region_type(region: str) -> str:
    if region in PROVINCES:
        return "province"
    return "city"


def location_evidence_id(school_name: str, province: str, city: str, city_status: str) -> str:
    raw = "|".join([school_name, province, city, city_status])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def iter_subject_rows() -> Iterable[Tuple[Dict[str, Any], Path]]:
    for path in SUBJECT_SOURCE_FILES:
        with path.open(encoding="utf-8") as f:
            rows = json.load(f)
        for row in rows:
            yield row, path


def infer_city(school_name: str) -> Tuple[str, str, List[str]]:
    normalized_name = normalize_text(school_name)
    if normalized_name in CITY_OVERRIDES:
        payload = CITY_OVERRIDES[normalized_name]
        return payload["city"], "override_reviewed", list(payload.get("aliases", []))
    if normalized_name in MULTI_CITY_REVIEW:
        return "", "review_multi_city", MULTI_CITY_REVIEW[normalized_name]
    for alias, city in CITY_ALIAS_TO_CITY.items():
        if alias in normalized_name:
            return city, "alias_in_school_name", [alias, city]
    for province in PROVINCES:
        if province in normalized_name:
            continue
    # If the school name begins with a region-like token, direct substring
    # checks during query will still catch it. We only store city when certain.
    return "", "unknown", []


def build_school_records() -> List[Dict[str, Any]]:
    by_school: Dict[str, Dict[str, Any]] = {}
    for row, source_path in iter_subject_rows():
        school_name = normalize_text(row.get("school_name", ""))
        province = normalize_region(str(row.get("province", "")))
        school_code = normalize_text(row.get("school_code", ""))
        if not school_name or not province:
            continue
        record = by_school.setdefault(
            school_name,
            {
                "school_name": school_name,
                "subject_school_codes": set(),
                "province": province,
                "source_files": set(),
            },
        )
        record["subject_school_codes"].add(school_code)
        record["source_files"].add(rel(source_path))
        if record["province"] != province:
            record["province"] = "REVIEW"

    records: List[Dict[str, Any]] = []
    for record in by_school.values():
        city, city_match_type, aliases = infer_city(record["school_name"])
        city_status = "PASS" if city else ("REVIEW" if city_match_type == "review_multi_city" else "UNKNOWN")
        source_files = sorted(record["source_files"])
        subject_school_codes = sorted(code for code in record["subject_school_codes"] if code)
        evidence_id = location_evidence_id(record["school_name"], record["province"], city, city_status)
        records.append(
            {
                "evidence_id": evidence_id,
                "school_name": record["school_name"],
                "subject_school_codes": "|".join(subject_school_codes),
                "province": record["province"],
                "province_source": "processed/选科要求 province",
                "city": city,
                "city_status": city_status,
                "city_match_type": city_match_type,
                "city_aliases": "|".join(sorted(set(aliases))),
                "source_files": "|".join(source_files),
                "quality_level": "A",
            }
        )
    records.sort(key=lambda x: (x["province"], x["school_name"]))
    return records


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS schools;
        CREATE TABLE schools (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT NOT NULL,
            school_name TEXT NOT NULL UNIQUE,
            subject_school_codes TEXT NOT NULL,
            province TEXT NOT NULL,
            province_source TEXT NOT NULL,
            city TEXT NOT NULL,
            city_status TEXT NOT NULL,
            city_match_type TEXT NOT NULL,
            city_aliases TEXT NOT NULL,
            source_files TEXT NOT NULL,
            quality_level TEXT NOT NULL
        );
        CREATE INDEX idx_schools_name ON schools (school_name);
        CREATE INDEX idx_schools_province ON schools (province);
        CREATE INDEX idx_schools_city ON schools (city);
        """
    )


def connect_region_index(db_path: Path = DEFAULT_REGION_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def row_to_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def find_school(
    conn: sqlite3.Connection,
    school_name: str = "",
    subject_school_code: str = "",
) -> Tuple[Optional[Dict[str, Any]], str]:
    normalized_name = normalize_text(school_name)
    normalized_code = normalize_text(subject_school_code)
    if normalized_code:
        rows = [
            row_to_record(row)
            for row in conn.execute(
                """
                SELECT * FROM schools
                WHERE subject_school_codes = ?
                   OR subject_school_codes LIKE ?
                   OR subject_school_codes LIKE ?
                   OR subject_school_codes LIKE ?
                """,
                (normalized_code, f"{normalized_code}|%", f"%|{normalized_code}", f"%|{normalized_code}|%"),
            )
        ]
        if len(rows) == 1:
            return rows[0], "subject_school_code"
        if len(rows) > 1:
            return None, "ambiguous_subject_school_code"
    if normalized_name:
        row = conn.execute("SELECT * FROM schools WHERE school_name = ?", (normalized_name,)).fetchone()
        if row:
            return row_to_record(row), "school_name"
    return None, "not_found"


def region_matches_record(record: Dict[str, Any], region: str) -> Dict[str, Any]:
    normalized_region = normalize_region(region)
    kind = region_type(normalized_region)
    if kind == "province":
        if record["province"] == normalized_region:
            return {
                "status": "MATCH",
                "matched": True,
                "reason_code": "PROVINCE_MATCH",
                "match_type": "province_exact",
                "matched_region": normalized_region,
            }
        return {
            "status": "NO_MATCH",
            "matched": False,
            "reason_code": "PROVINCE_MISMATCH",
            "match_type": "province_exact",
            "matched_region": "",
        }

    city = normalize_region(record.get("city", ""))
    aliases = {normalize_region(item) for item in str(record.get("city_aliases", "")).split("|") if item}
    school_name = normalize_text(record.get("school_name", ""))
    if record.get("city_status") == "REVIEW" and (normalized_region in aliases or normalized_region in school_name):
        return {
            "status": "REVIEW",
            "matched": None,
            "reason_code": "MULTI_CITY_REVIEW",
            "match_type": "city_ambiguous",
            "matched_region": normalized_region,
        }
    if record.get("city_status") == "REVIEW":
        return {
            "status": "REVIEW",
            "matched": None,
            "reason_code": "CITY_UNKNOWN_MULTI_CAMPUS",
            "match_type": "city_ambiguous",
            "matched_region": "",
        }
    if city == normalized_region or normalized_region in aliases or normalized_region in school_name:
        return {
            "status": "MATCH",
            "matched": True,
            "reason_code": "CITY_MATCH",
            "match_type": record.get("city_match_type") or "city_name",
            "matched_region": normalized_region,
        }
    return {
        "status": "NO_MATCH",
        "matched": False,
        "reason_code": "CITY_MISMATCH",
        "match_type": "city_exact_or_alias",
        "matched_region": "",
    }


def check_school_regions(
    regions: Sequence[str],
    school_name: str = "",
    subject_school_code: str = "",
    db_path: Path = DEFAULT_REGION_DB_PATH,
) -> Dict[str, Any]:
    normalized_regions = [normalize_region(region) for region in regions if normalize_region(region)]
    if not normalized_regions:
        return {
            "status": "REVIEW",
            "matched": None,
            "reason_code": "MISSING_REGION",
            "match_type": "none",
        }

    with connect_region_index(db_path) as conn:
        record, lookup_type = find_school(conn, school_name=school_name, subject_school_code=subject_school_code)

    if record is None:
        return {
            "status": "REVIEW",
            "matched": None,
            "reason_code": lookup_type.upper(),
            "match_type": lookup_type,
            "school_name": normalize_text(school_name),
            "subject_school_code": normalize_text(subject_school_code),
            "regions": normalized_regions,
        }

    checks = [region_matches_record(record, region) for region in normalized_regions]
    match = next((item for item in checks if item["status"] == "MATCH"), None)
    review = next((item for item in checks if item["status"] == "REVIEW"), None)
    final = match or review or checks[0]
    return {
        "status": final["status"],
        "matched": final["matched"],
        "reason_code": final["reason_code"],
        "match_type": final["match_type"],
        "matched_region": final["matched_region"],
        "regions": normalized_regions,
        "lookup_type": lookup_type,
        "school_name": record["school_name"],
        "subject_school_codes": record["subject_school_codes"],
        "province": record["province"],
        "city": record["city"],
        "city_status": record["city_status"],
        "city_match_type": record["city_match_type"],
        "city_aliases": record["city_aliases"],
        "evidence_id": record["evidence_id"],
        "source_files": record["source_files"],
        "quality_level": record["quality_level"],
        "all_region_checks": checks,
    }
