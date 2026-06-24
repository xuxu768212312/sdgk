#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic subject-requirement index and eligibility checks."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sdgk.core.paths import ROOT

REQ_DIR = ROOT / "processed" / "选科要求"
DEFAULT_DB_PATH = REQ_DIR / "subject_index.sqlite"
DEFAULT_META_PATH = REQ_DIR / "subject_index_meta.json"

SOURCE_DATASETS = [
    ("2024", "本科", REQ_DIR / "2024版本科.json"),
    ("2024", "专科", REQ_DIR / "2024版专科.json"),
    ("2027", "本科", REQ_DIR / "2027版本科.json"),
    ("2027", "专科", REQ_DIR / "2027版专科.json"),
]

CN_SUBJECTS = ["物理", "化学", "生物", "思想政治", "历史", "地理"]
CN_SUBJECT_SET = set(CN_SUBJECTS)
SUBJECT_ALIASES = {
    "物理": "物理",
    "物": "物理",
    "化学": "化学",
    "化": "化学",
    "生物": "生物",
    "生": "生物",
    "思想政治": "思想政治",
    "政治": "思想政治",
    "政": "思想政治",
    "历史": "历史",
    "史": "历史",
    "地理": "地理",
    "地": "地理",
}

ALLOWED_TYPES = {"none", "one", "two", "three", "any"}
PASS_STATUS = "PASS"
BLOCK_STATUS = "BLOCK"
REVIEW_STATUS = "REVIEW"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_subject_requirement(raw: str) -> Tuple[str, List[str]]:
    """Parse official raw subject text into the normalized requirement type.

    This mirrors the existing PDF extraction/audit logic:
    - "不提科目要求" => none
    - comma-separated subjects => all required
    - "或" separated subjects => any one subject is enough
    """

    if not raw:
        return "none", []
    s = str(raw).strip()
    if "不提科目要求" in s:
        return "none", []
    m = re.match(r"^([^()（）]+)[\(（]", s)
    if not m:
        return "none", []
    subjects_str = m.group(1).strip()
    if "或" in subjects_str:
        subjects = [x.strip() for x in subjects_str.split("或") if x.strip()]
        subjects = [x for x in subjects if x in CN_SUBJECT_SET]
        if len(subjects) >= 2:
            return "any", subjects
    subjects = re.split(r"[,，]", subjects_str)
    subjects = [x.strip() for x in subjects if x.strip()]
    subjects = [x for x in subjects if x in CN_SUBJECT_SET]
    if len(subjects) == 0:
        return "none", []
    if len(subjects) == 1:
        return "one", subjects
    if len(subjects) == 2:
        return "two", subjects
    if len(subjects) == 3:
        return "three", subjects
    return "none", []


def split_subjects_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [x.strip() for x in text.split("|") if x.strip()]


def normalize_subjects(subjects: Any) -> Tuple[List[str], List[str]]:
    """Normalize subject input to official Chinese names.

    Returns (subjects, invalid_tokens). The output preserves first occurrence
    order and removes duplicates.
    """

    if isinstance(subjects, str):
        tokens = [x.strip() for x in re.split(r"[,+，、/\\|\s]+", subjects) if x.strip()]
    elif isinstance(subjects, Sequence):
        tokens = [str(x).strip() for x in subjects if str(x).strip()]
    else:
        tokens = []

    normalized: List[str] = []
    invalid: List[str] = []
    for token in tokens:
        canonical = SUBJECT_ALIASES.get(token)
        if canonical is None:
            invalid.append(token)
            continue
        if canonical not in normalized:
            normalized.append(canonical)
    return normalized, invalid


def normalize_level(level: str) -> Optional[str]:
    text = str(level or "").strip()
    if text in {"本科", "本"}:
        return "本科"
    if text in {"专科", "高职", "高职专科", "专"}:
        return "专科"
    return None


def resolve_edition(year: Optional[int] = None, edition: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    if edition is not None and str(edition).strip():
        text = str(edition).strip()
        if text in {"2024", "2024版"}:
            return "2024", None
        if text in {"2027", "2027版"}:
            return "2027", None
        return None, "UNSUPPORTED_EDITION"
    if year is None:
        return None, "YEAR_OR_EDITION_REQUIRED"
    if year in (2025, 2026):
        return "2024", None
    if year >= 2027:
        return "2027", None
    return None, "YEAR_EDITION_UNRESOLVED"


def make_evidence_id(row: Dict[str, Any]) -> str:
    parts = [
        str(row.get("edition", "")).strip(),
        str(row.get("level", "")).strip(),
        str(row.get("school_code", "")).strip(),
        str(row.get("major_code", "")).strip(),
        str(row.get("major_name", "")).strip(),
        str(row.get("subject_requirement_raw", "")).strip(),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def source_files() -> List[Tuple[str, str, Path]]:
    return SOURCE_DATASETS[:]


def iter_source_rows() -> Iterable[Tuple[Dict[str, Any], Path]]:
    for expected_edition, expected_level, path in source_files():
        rows = read_json(path)
        if not isinstance(rows, list):
            raise ValueError(f"{rel(path)} is not a JSON list")
        for row in rows:
            copied = dict(row)
            copied["edition"] = str(copied.get("edition", expected_edition)).strip()
            copied["level"] = str(copied.get("level", expected_level)).strip()
            yield copied, path


def validate_requirement_row(row: Dict[str, Any], path: Path) -> List[str]:
    errors: List[str] = []
    if not re.match(r"^\d{5}$", str(row.get("school_code", "")).strip()):
        errors.append("school_code must be a 5-digit code")
    if str(row.get("subject_requirement_type", "")).strip() not in ALLOWED_TYPES:
        errors.append("subject_requirement_type is invalid")
    subjects = split_subjects_list(row.get("subjects_list", ""))
    invalid_subjects = [s for s in subjects if s not in CN_SUBJECT_SET]
    if invalid_subjects:
        errors.append(f"invalid subject names: {','.join(invalid_subjects)}")
    expected_type, expected_subjects = parse_subject_requirement(str(row.get("subject_requirement_raw", "")))
    if str(row.get("subject_requirement_type", "")).strip() != expected_type or subjects != expected_subjects:
        errors.append("structured fields do not match subject_requirement_raw")
    if not str(row.get("school_name", "")).strip():
        errors.append("school_name is empty")
    if not str(row.get("major_name", "")).strip():
        errors.append("major_name is empty")
    if errors:
        errors = [f"{rel(path)} {row.get('school_code', '')} {row.get('major_code', '')}: {e}" for e in errors]
    return errors


def connect_index(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS requirements;
        CREATE TABLE requirements (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT NOT NULL,
            edition TEXT NOT NULL,
            level TEXT NOT NULL,
            school_code TEXT NOT NULL,
            school_name TEXT NOT NULL,
            major_code TEXT NOT NULL,
            major_name TEXT NOT NULL,
            subject_requirement_raw TEXT NOT NULL,
            subject_requirement_type TEXT NOT NULL,
            subjects_list TEXT NOT NULL,
            province TEXT NOT NULL,
            source_file TEXT NOT NULL,
            quality_level TEXT NOT NULL
        );
        CREATE INDEX idx_requirements_code
            ON requirements (edition, level, school_code, major_code);
        CREATE INDEX idx_requirements_name
            ON requirements (edition, level, school_name, major_name);
        CREATE INDEX idx_requirements_evidence
            ON requirements (evidence_id);
        """
    )


def row_to_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def evidence_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "evidence_id": record.get("evidence_id"),
        "edition": record.get("edition"),
        "level": record.get("level"),
        "school_code": record.get("school_code"),
        "school_name": record.get("school_name"),
        "major_code": record.get("major_code"),
        "major_name": record.get("major_name"),
        "subject_requirement_raw": record.get("subject_requirement_raw"),
        "subject_requirement_type": record.get("subject_requirement_type"),
        "subjects_list": record.get("subjects_list"),
        "source_file": record.get("source_file"),
        "quality_level": record.get("quality_level"),
    }


def base_result(
    status: str,
    eligible: Optional[bool],
    reason_code: str,
    match_type: str,
    message: str,
    **extra: Any,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": status,
        "eligible": eligible,
        "reason_code": reason_code,
        "match_type": match_type,
        "message": message,
        "evidence_id": None,
        "source_file": None,
        "evidence": None,
    }
    result.update(extra)
    return result


def evaluate_record(record: Dict[str, Any], subjects: List[str], match_type: str) -> Dict[str, Any]:
    req_type = str(record.get("subject_requirement_type", "")).strip()
    required = split_subjects_list(record.get("subjects_list", ""))
    subject_set = set(subjects)

    if req_type == "none":
        status = PASS_STATUS
        eligible = True
        reason = "NO_SUBJECT_REQUIRED"
        message = "不提科目要求，任意选科组合均可报。"
    elif req_type in {"one", "two", "three"}:
        missing = [s for s in required if s not in subject_set]
        if missing:
            status = BLOCK_STATUS
            eligible = False
            reason = "MISSING_REQUIRED_SUBJECT"
            message = "缺少必须选考科目：" + "、".join(missing)
        else:
            status = PASS_STATUS
            eligible = True
            reason = "REQUIRED_SUBJECTS_INCLUDED"
            message = "已包含全部必须选考科目：" + ("、".join(required) if required else "无")
    elif req_type == "any":
        matched = [s for s in required if s in subject_set]
        if matched:
            status = PASS_STATUS
            eligible = True
            reason = "ANY_SUBJECT_INCLUDED"
            message = "已包含任选科目之一：" + "、".join(matched)
        else:
            status = BLOCK_STATUS
            eligible = False
            reason = "MISSING_ANY_SUBJECT"
            message = "未包含任选科目中的任何一门：" + "、".join(required)
    else:
        return base_result(
            REVIEW_STATUS,
            None,
            "UNSUPPORTED_REQUIREMENT_TYPE",
            match_type,
            "选科要求类型无法识别，必须人工复核。",
        )

    evidence = evidence_from_record(record)
    return {
        "status": status,
        "eligible": eligible,
        "reason_code": reason,
        "match_type": match_type,
        "message": message,
        "evidence_id": evidence["evidence_id"],
        "source_file": evidence["source_file"],
        "evidence": evidence,
    }


def fetch_matches(
    conn: sqlite3.Connection,
    edition: str,
    level: str,
    school_code: Optional[str],
    major_code: Optional[str],
    school_name: Optional[str],
    major_name: Optional[str],
) -> Tuple[List[Dict[str, Any]], str]:
    if school_code and major_code:
        rows = conn.execute(
            """
            SELECT * FROM requirements
            WHERE edition = ? AND level = ? AND school_code = ? AND major_code = ?
            ORDER BY school_name, major_name, row_id
            """,
            (edition, level, school_code.strip(), major_code.strip()),
        ).fetchall()
        if rows:
            return [row_to_record(r) for r in rows], "exact_code"
        if not (school_name and major_name):
            return [], "exact_code"

    if school_name and major_name:
        rows = conn.execute(
            """
            SELECT * FROM requirements
            WHERE edition = ? AND level = ? AND school_name = ? AND major_name = ?
            ORDER BY school_code, major_code, row_id
            """,
            (edition, level, school_name.strip(), major_name.strip()),
        ).fetchall()
        match_type = "unique_name_after_code_miss" if school_code and major_code else "unique_name"
        return [row_to_record(r) for r in rows], match_type

    return [], "none"


def check_eligibility(
    *,
    year: Optional[int] = None,
    edition: Optional[str] = None,
    level: str,
    subjects: Any,
    school_code: Optional[str] = None,
    major_code: Optional[str] = None,
    school_name: Optional[str] = None,
    major_name: Optional[str] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    resolved_edition, edition_error = resolve_edition(year=year, edition=edition)
    normalized_level = normalize_level(level)
    normalized_subjects, invalid_subjects = normalize_subjects(subjects)

    context = {
        "year": year,
        "edition": resolved_edition,
        "level": normalized_level,
        "subjects": normalized_subjects,
        "school_code": (school_code or "").strip() or None,
        "major_code": (major_code or "").strip() or None,
        "school_name": (school_name or "").strip() or None,
        "major_name": (major_name or "").strip() or None,
    }

    if edition_error:
        return base_result(
            REVIEW_STATUS,
            None,
            edition_error,
            "none",
            "年份无法映射到选科要求版本，必须人工复核。",
            context=context,
        )
    if normalized_level is None:
        return base_result(
            REVIEW_STATUS,
            None,
            "INVALID_LEVEL",
            "none",
            "层次必须是本科或专科。",
            context=context,
        )
    if invalid_subjects or len(normalized_subjects) != 3:
        return base_result(
            REVIEW_STATUS,
            None,
            "INVALID_SUBJECT_INPUT",
            "none",
            "选科必须是 3 个有效科目。",
            context=context,
            invalid_subjects=invalid_subjects,
        )
    if not db_path.exists():
        return base_result(
            REVIEW_STATUS,
            None,
            "INDEX_MISSING",
            "none",
            f"选科索引不存在：{rel(db_path)}",
            context=context,
        )
    if not ((school_code and major_code) or (school_name and major_name)):
        return base_result(
            REVIEW_STATUS,
            None,
            "MISSING_LOOKUP_KEYS",
            "none",
            "必须提供院校代码+专业代码，或院校名称+专业名称。",
            context=context,
        )

    with connect_index(db_path) as conn:
        matches, match_type = fetch_matches(
            conn,
            resolved_edition or "",
            normalized_level,
            context["school_code"],
            context["major_code"],
            context["school_name"],
            context["major_name"],
        )

    if not matches:
        return base_result(
            REVIEW_STATUS,
            None,
            "NO_REQUIREMENT_ROW",
            match_type,
            "未在选科要求索引中命中该院校专业，必须人工复核。",
            context=context,
        )
    if len(matches) > 1:
        return base_result(
            REVIEW_STATUS,
            None,
            "AMBIGUOUS_REQUIREMENT_ROW",
            match_type,
            "命中多条选科要求记录，必须人工复核，不能自动判断。",
            context=context,
            matches_count=len(matches),
            sample_evidence=[evidence_from_record(r) for r in matches[:10]],
        )

    result = evaluate_record(matches[0], normalized_subjects, match_type)
    result["context"] = context
    return result
