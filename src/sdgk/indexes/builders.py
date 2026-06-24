from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from sdgk.core.evidence import stable_hash
from sdgk.core.io import read_json, write_json
from sdgk.core.paths import PROCESSED_DIR, ROOT, rel
from sdgk.indexes import region as region_index
from sdgk.indexes import subject as subject_index


MASTER_DIR = PROCESSED_DIR / "master"
DEFAULT_MASTER_DB_PATH = MASTER_DIR / "master_index.sqlite"
DEFAULT_MASTER_META_PATH = MASTER_DIR / "master_index_meta.json"


def build_subject_index(
    db_path: Path = subject_index.DEFAULT_DB_PATH,
    meta_path: Path = subject_index.DEFAULT_META_PATH,
    rebuild: bool = False,
) -> dict[str, Any]:
    if db_path.exists() and not rebuild:
        raise FileExistsError(f"{rel(db_path)} already exists; pass --rebuild to replace it")
    tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    validation_errors: list[str] = []
    records: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}

    for row, source_path in subject_index.iter_source_rows():
        errors = subject_index.validate_requirement_row(row, source_path)
        if errors:
            validation_errors.extend(errors)
            if len(validation_errors) >= 20:
                break
        record = {
            "evidence_id": subject_index.make_evidence_id(row),
            "edition": str(row.get("edition", "")).strip(),
            "level": str(row.get("level", "")).strip(),
            "school_code": str(row.get("school_code", "")).strip(),
            "school_name": str(row.get("school_name", "")).strip(),
            "major_code": str(row.get("major_code", "")).strip(),
            "major_name": str(row.get("major_name", "")).strip(),
            "subject_requirement_raw": str(row.get("subject_requirement_raw", "")).strip(),
            "subject_requirement_type": str(row.get("subject_requirement_type", "")).strip(),
            "subjects_list": str(row.get("subjects_list", "")).strip(),
            "province": str(row.get("province", "")).strip(),
            "source_file": rel(source_path),
            "quality_level": "A",
        }
        records.append(record)
        source_counts[rel(source_path)] = source_counts.get(rel(source_path), 0) + 1

    if validation_errors:
        raise ValueError("subject requirement validation failed:\n" + "\n".join(validation_errors))

    expected_total = sum(source_counts.values())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(tmp_path)) as conn:
        subject_index.create_schema(conn)
        conn.executemany(
            """
            INSERT INTO requirements (
                evidence_id, edition, level, school_code, school_name, major_code,
                major_name, subject_requirement_raw, subject_requirement_type,
                subjects_list, province, source_file, quality_level
            )
            VALUES (
                :evidence_id, :edition, :level, :school_code, :school_name, :major_code,
                :major_name, :subject_requirement_raw, :subject_requirement_type,
                :subjects_list, :province, :source_file, :quality_level
            )
            """,
            records,
        )
        actual_total = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
        if actual_total != expected_total:
            raise RuntimeError(f"index row count mismatch: expected {expected_total}, got {actual_total}")
        conn.execute("PRAGMA optimize")
    tmp_path.replace(db_path)

    meta = {
        "dataset": "选科要求 SQLite 索引",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "db_file": rel(db_path),
        "row_count": expected_total,
        "source_counts": source_counts,
        "source_files": [rel(path) for _, _, path in subject_index.source_files()],
        "publisher": "山东省教育招生考试院",
        "official_domain": "sdzk.cn",
        "quality_level": "A",
        "verification_status": "derived_from_processed_subject_requirements",
        "evidence_id_formula": "sha256(edition|level|school_code|major_code|major_name|subject_requirement_raw)",
        "hard_gate_policy": "志愿方案中任何 BLOCK 或 REVIEW 均不得作为正式交付方案。",
    }
    write_json(meta_path, meta)
    return meta


def build_region_index(
    db_path: Path = region_index.DEFAULT_REGION_DB_PATH,
    meta_path: Path = region_index.DEFAULT_REGION_META_PATH,
    rebuild: bool = False,
) -> dict[str, Any]:
    if db_path.exists() and not rebuild:
        raise FileExistsError(f"{rel(db_path)} already exists; pass --rebuild to replace it")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    records = region_index.build_school_records()
    with sqlite3.connect(str(tmp_path)) as conn:
        region_index.create_schema(conn)
        conn.executemany(
            """
            INSERT INTO schools (
                evidence_id, school_name, subject_school_codes, province,
                province_source, city, city_status, city_match_type,
                city_aliases, source_files, quality_level
            )
            VALUES (
                :evidence_id, :school_name, :subject_school_codes, :province,
                :province_source, :city, :city_status, :city_match_type,
                :city_aliases, :source_files, :quality_level
            )
            """,
            records,
        )
        actual = conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0]
        if actual != len(records):
            raise RuntimeError(f"school region row count mismatch: expected {len(records)}, got {actual}")
        conn.execute("PRAGMA optimize")
    tmp_path.replace(db_path)

    meta = {
        "dataset": "院校地区 SQLite 索引",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "db_file": rel(db_path),
        "row_count": len(records),
        "source_files": [rel(path) for path in region_index.SUBJECT_SOURCE_FILES],
        "province_source": "processed/选科要求/*.json province 字段",
        "province_quality_level": "A",
        "city_policy": "城市仅在学校名显式地名或 reviewed override 时 PASS；多校区/不确定返回 REVIEW",
        "hard_gate_policy": "地区筛选不得使用 school_name contains 省名；省份必须查 province，城市不确定必须 REVIEW。",
    }
    write_json(meta_path, meta)
    return meta


def normalize_name(value: Any) -> str:
    return str(value or "").strip().replace("（", "(").replace("）", ")").replace("　", "").replace(" ", "")


def normalize_code(value: Any) -> str:
    return str(value or "").strip().upper()


def school_code_system(code: str) -> str:
    if re.match(r"^\d{5}$", code):
        return "subject_5_digit"
    if re.match(r"^[A-Z]\d{3,4}$", code):
        return "admission_school_code"
    if code:
        return "school_code_other"
    return "missing"


def major_code_system(code: str) -> str:
    if re.match(r"^\d{4}$", code):
        return "subject_major_code"
    if re.match(r"^[A-Z0-9]{1,6}$", code):
        return "program_major_code"
    if code:
        return "major_code_other"
    return "missing"


def major_tags(major_name: str) -> dict[str, Any]:
    name = normalize_name(major_name)
    law_scan_name = name.replace("书法学", "")
    is_teacher = "师范" in name or name in {"小学教育", "学前教育", "特殊教育", "教育学", "教育技术学", "科学教育"}
    is_law = (
        law_scan_name == "法学"
        or law_scan_name.startswith("法学(")
        or "法学类" in law_scan_name
        or "法学试验" in law_scan_name
        or "法学双" in law_scan_name
        or "含法学" in law_scan_name
        or any(token in law_scan_name for token in ("知识产权", "马克思主义理论", "政治学", "国际政治"))
    )
    is_english = "英语" in name or "商务英语" in name or "翻译" in name
    is_finance = any(token in name for token in ("金融", "会计", "财务", "审计", "经济", "财政", "保险", "投资", "税收", "国际经济与贸易"))
    is_bio_related = any(token in name for token in ("生物", "食品", "药学", "制药", "医学", "园林", "农学", "生态", "动物", "植物"))
    preference_tags: list[str] = []
    if is_teacher:
        preference_tags.append("师范")
    if is_law:
        preference_tags.append("法学")
    if is_english:
        preference_tags.append("英语")
    if is_finance:
        preference_tags.append("金融")
    if is_bio_related:
        preference_tags.append("生物相关")
        if "生物工程" in name:
            preference_tags.append("生物工程")
    family = "其他"
    if is_teacher:
        family = "师范教育"
    elif is_law:
        family = "法学政法"
    elif is_english:
        family = "外语英语"
    elif is_finance:
        family = "财经金融"
    elif is_bio_related:
        family = "生物医农"
    return {
        "major_family": family,
        "is_teacher": int(is_teacher),
        "is_law": int(is_law),
        "is_english": int(is_english),
        "is_finance": int(is_finance),
        "is_bio_related": int(is_bio_related),
        "preference_tags": "|".join(preference_tags),
        "classification_status": "PASS" if family != "其他" else "REVIEW",
    }


def create_master_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS evidence;
        DROP TABLE IF EXISTS plan_history;
        DROP TABLE IF EXISTS admission_history;
        DROP TABLE IF EXISTS programs;
        DROP TABLE IF EXISTS major_code_aliases;
        DROP TABLE IF EXISTS school_code_aliases;
        DROP TABLE IF EXISTS majors;
        DROP TABLE IF EXISTS schools;

        CREATE TABLE schools (
            school_id TEXT PRIMARY KEY,
            school_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            subject_school_codes TEXT NOT NULL,
            admission_school_codes TEXT NOT NULL,
            province TEXT NOT NULL,
            city TEXT NOT NULL,
            city_status TEXT NOT NULL,
            school_level_tag TEXT NOT NULL,
            ownership_tag TEXT NOT NULL,
            subject_school_code_count INTEGER NOT NULL,
            admission_school_code_count INTEGER NOT NULL,
            program_count INTEGER NOT NULL,
            code_status TEXT NOT NULL,
            source_files TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_schools_name ON schools(normalized_name);
        CREATE INDEX idx_master_schools_province ON schools(province);
        CREATE INDEX idx_master_schools_code_status ON schools(code_status);

        CREATE TABLE school_code_aliases (
            alias_id TEXT PRIMARY KEY,
            school_id TEXT NOT NULL,
            school_name TEXT NOT NULL,
            school_code TEXT NOT NULL,
            code_system TEXT NOT NULL,
            source_files TEXT NOT NULL,
            usage_count INTEGER NOT NULL,
            ambiguity_status TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_school_code_aliases_code ON school_code_aliases(school_code, code_system);

        CREATE TABLE majors (
            major_id TEXT PRIMARY KEY,
            major_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            major_code_samples TEXT NOT NULL,
            major_family TEXT NOT NULL,
            is_teacher INTEGER NOT NULL,
            is_law INTEGER NOT NULL,
            is_english INTEGER NOT NULL,
            is_finance INTEGER NOT NULL,
            is_bio_related INTEGER NOT NULL,
            preference_tags TEXT NOT NULL,
            classification_status TEXT NOT NULL,
            major_code_count INTEGER NOT NULL,
            program_count INTEGER NOT NULL,
            code_status TEXT NOT NULL,
            source_files TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_majors_name ON majors(normalized_name);
        CREATE INDEX idx_master_majors_family ON majors(major_family);
        CREATE INDEX idx_master_majors_code_status ON majors(code_status);

        CREATE TABLE major_code_aliases (
            alias_id TEXT PRIMARY KEY,
            major_id TEXT NOT NULL,
            major_name TEXT NOT NULL,
            major_code TEXT NOT NULL,
            code_system TEXT NOT NULL,
            source_files TEXT NOT NULL,
            usage_count INTEGER NOT NULL,
            ambiguity_status TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_major_code_aliases_code ON major_code_aliases(major_code, code_system);

        CREATE TABLE programs (
            program_id TEXT PRIMARY KEY,
            school_id TEXT NOT NULL,
            major_id TEXT NOT NULL,
            school_code TEXT NOT NULL,
            major_code TEXT NOT NULL,
            school_name TEXT NOT NULL,
            major_name TEXT NOT NULL,
            level TEXT NOT NULL,
            year INTEGER NOT NULL,
            round INTEGER NOT NULL,
            batch TEXT NOT NULL,
            category TEXT NOT NULL,
            plan_count INTEGER,
            min_rank INTEGER,
            subject_check_status TEXT NOT NULL,
            region_check_status TEXT NOT NULL,
            source_quality TEXT NOT NULL,
            source_file TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_programs_year ON programs(year, round, level);
        CREATE INDEX idx_master_programs_school ON programs(school_name);
        CREATE INDEX idx_master_programs_major ON programs(major_name);

        CREATE TABLE admission_history (
            program_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            round INTEGER NOT NULL,
            school_code TEXT NOT NULL,
            major_code TEXT NOT NULL,
            plan_count INTEGER,
            min_rank INTEGER,
            source_file TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_admission_program ON admission_history(program_id);

        CREATE TABLE plan_history (
            program_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            batch TEXT NOT NULL,
            category TEXT NOT NULL,
            school_code TEXT NOT NULL,
            major_code TEXT NOT NULL,
            plan_count INTEGER,
            source_file TEXT NOT NULL,
            evidence_id TEXT NOT NULL
        );
        CREATE INDEX idx_master_plan_program ON plan_history(program_id);

        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            quality_level TEXT NOT NULL,
            source_url TEXT NOT NULL,
            payload_hash TEXT NOT NULL
        );
        """
    )


def load_region_records() -> dict[str, dict[str, Any]]:
    if not region_index.DEFAULT_REGION_DB_PATH.exists():
        return {}
    with sqlite3.connect(str(region_index.DEFAULT_REGION_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        return {row["school_name"]: dict(row) for row in conn.execute("SELECT * FROM schools")}


def school_level_tag(name: str) -> str:
    if any(token in name for token in ("职业技术大学", "职业大学")):
        return "职业本科"
    if "大学" in name:
        return "本科大学"
    if "学院" in name:
        return "本科院校"
    if any(token in name for token in ("职业技术学院", "高等专科学校", "专科学校")):
        return "高职专科"
    return "REVIEW"


def build_master_index(
    db_path: Path = DEFAULT_MASTER_DB_PATH,
    meta_path: Path = DEFAULT_MASTER_META_PATH,
    rebuild: bool = False,
) -> dict[str, Any]:
    if db_path.exists() and not rebuild:
        raise FileExistsError(f"{rel(db_path)} already exists; pass --rebuild to replace it")
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    regions = load_region_records()
    subject_rows = []
    for row, source_path in subject_index.iter_source_rows():
        copied = dict(row)
        copied["source_file"] = rel(source_path)
        subject_rows.append(copied)

    admission_rows: list[dict[str, Any]] = []
    for path in sorted((PROCESSED_DIR / "投档表").glob("20??_round*.json")):
        year_match = re.search(r"(\d{4})_round(\d)", path.name)
        if not year_match:
            continue
        rows = read_json(path)
        for row in rows:
            copied = dict(row)
            copied["source_file"] = rel(path)
            copied["level"] = "本科" if int(copied.get("round", 0)) == 1 else "本专科"
            copied["batch"] = "常规批"
            copied["category"] = "普通类"
            admission_rows.append(copied)

    plan_rows: list[dict[str, Any]] = []
    for path in sorted((PROCESSED_DIR / "志愿计划").glob("20??.json")):
        rows = read_json(path)
        for row in rows:
            copied = dict(row)
            copied["source_file"] = rel(path)
            copied["round"] = 2 if "第2次" in copied.get("batch", "") else (3 if "第3次" in copied.get("batch", "") else 0)
            copied["level"] = copied.get("level") or ("本科" if "本科" in copied.get("batch", "") else "")
            plan_rows.append(copied)

    latest_program_year = max(
        [int(row.get("year") or 0) for row in admission_rows + plan_rows],
        default=0,
    )
    latest_program_keys: set[tuple[Any, ...]] = set()
    school_program_counts: dict[str, int] = defaultdict(int)
    major_program_counts: dict[str, int] = defaultdict(int)
    for row in admission_rows + plan_rows:
        if int(row.get("year") or 0) != latest_program_year:
            continue
        school_name = normalize_name(row.get("school_name"))
        major_name = normalize_name(row.get("major_name"))
        key = (
            str(row.get("level") or ""),
            int(row.get("year") or 0),
            int(row.get("round") or 0),
            str(row.get("batch") or ""),
            normalize_code(row.get("school_code")),
            normalize_code(row.get("major_code")),
            school_name,
            major_name,
        )
        if key in latest_program_keys:
            continue
        latest_program_keys.add(key)
        if school_name:
            school_program_counts[school_name] += 1
        if major_name:
            major_program_counts[major_name] += 1

    school_codes: dict[str, set[str]] = defaultdict(set)
    school_sources: dict[str, set[str]] = defaultdict(set)
    major_codes: dict[str, set[str]] = defaultdict(set)
    major_sources: dict[str, set[str]] = defaultdict(set)
    school_alias_sources: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    school_alias_usage: dict[tuple[str, str, str], int] = defaultdict(int)
    school_code_to_names: dict[tuple[str, str], set[str]] = defaultdict(set)
    major_alias_sources: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    major_alias_usage: dict[tuple[str, str, str], int] = defaultdict(int)
    major_code_to_names: dict[tuple[str, str], set[str]] = defaultdict(set)
    for rows, include_major_alias in ((subject_rows, False), (admission_rows, True), (plan_rows, True)):
        for row in rows:
            school_name = normalize_name(row.get("school_name"))
            major_name = normalize_name(row.get("major_name"))
            school_code = normalize_code(row.get("school_code"))
            major_code = normalize_code(row.get("major_code"))
            source_file = str(row.get("source_file", "")).strip()
            if school_name:
                school_codes[school_name].add(school_code)
                school_sources[school_name].add(source_file)
                if school_code:
                    system = school_code_system(school_code)
                    alias_key = (school_name, school_code, system)
                    school_alias_sources[alias_key].add(source_file)
                    school_alias_usage[alias_key] += 1
                    school_code_to_names[(system, school_code)].add(school_name)
            if major_name:
                major_codes[major_name].add(major_code)
                major_sources[major_name].add(source_file)
                if major_code and include_major_alias and int(row.get("year") or 0) == latest_program_year:
                    system = major_code_system(major_code)
                    alias_key = (major_name, major_code, system)
                    major_alias_sources[alias_key].add(source_file)
                    major_alias_usage[alias_key] += 1
                    major_code_to_names[(system, major_code)].add(major_name)

    schools: list[dict[str, Any]] = []
    school_id_by_name: dict[str, str] = {}
    for school_name in sorted(school_codes):
        region = regions.get(school_name, {})
        codes = sorted(code for code in school_codes[school_name] if code)
        subject_codes = sorted(code for code in str(region.get("subject_school_codes", "")).split("|") if code)
        subject_code_set = set(subject_codes) | {code for code in codes if school_code_system(code) == "subject_5_digit"}
        admission_code_set = {code for code in codes if school_code_system(code) != "subject_5_digit"}
        code_status = "PASS"
        if not codes and not subject_code_set:
            code_status = "REVIEW"
        elif any(len(school_code_to_names[(school_code_system(code), code)]) > 1 for code in codes):
            code_status = "REVIEW"
        school_id = stable_hash("school", school_name)
        school_id_by_name[school_name] = school_id
        schools.append(
            {
                "school_id": school_id,
                "school_name": school_name,
                "normalized_name": school_name,
                "subject_school_codes": "|".join(subject_codes),
                "admission_school_codes": "|".join(codes),
                "province": region.get("province", ""),
                "city": region.get("city", ""),
                "city_status": region.get("city_status", "UNKNOWN") or "UNKNOWN",
                "school_level_tag": school_level_tag(school_name),
                "ownership_tag": "REVIEW",
                "subject_school_code_count": len(subject_code_set),
                "admission_school_code_count": len(admission_code_set),
                "program_count": school_program_counts.get(school_name, 0),
                "code_status": code_status,
                "source_files": "|".join(sorted(school_sources[school_name])),
                "evidence_id": stable_hash("school", school_name, region.get("province", ""), "|".join(codes)),
            }
        )

    majors: list[dict[str, Any]] = []
    major_id_by_name: dict[str, str] = {}
    for major_name in sorted(major_codes):
        tags = major_tags(major_name)
        major_id = stable_hash("major", major_name)
        major_id_by_name[major_name] = major_id
        majors.append(
            {
                "major_id": major_id,
                "major_name": major_name,
                "normalized_name": major_name,
                "major_code_samples": "|".join(sorted(code for code in major_codes[major_name] if code)[:30]),
                "major_code_count": len([code for code in major_codes[major_name] if code]),
                "program_count": major_program_counts.get(major_name, 0),
                "code_status": "PASS" if any(code for code in major_codes[major_name]) else "REVIEW",
                "source_files": "|".join(sorted(major_sources[major_name])),
                "evidence_id": stable_hash("major", major_name, tags["major_family"]),
                **tags,
            }
        )

    school_code_aliases: list[dict[str, Any]] = []
    for (school_name, code, system), sources in sorted(school_alias_sources.items()):
        school_id = school_id_by_name.get(school_name, stable_hash("school", school_name))
        ambiguity_status = "PASS" if len(school_code_to_names[(system, code)]) == 1 else "REVIEW"
        school_code_aliases.append(
            {
                "alias_id": stable_hash("school_code_alias", school_id, code, system),
                "school_id": school_id,
                "school_name": school_name,
                "school_code": code,
                "code_system": system,
                "source_files": "|".join(sorted(sources)),
                "usage_count": school_alias_usage[(school_name, code, system)],
                "ambiguity_status": ambiguity_status,
                "evidence_id": stable_hash("school_code_alias", school_name, code, system, ambiguity_status),
            }
        )

    major_code_aliases: list[dict[str, Any]] = []
    for (major_name, code, system), sources in sorted(major_alias_sources.items()):
        major_id = major_id_by_name.get(major_name, stable_hash("major", major_name))
        ambiguity_status = "PASS" if len(major_code_to_names[(system, code)]) == 1 else "REVIEW"
        major_code_aliases.append(
            {
                "alias_id": stable_hash("major_code_alias", major_id, code, system),
                "major_id": major_id,
                "major_name": major_name,
                "major_code": code,
                "code_system": system,
                "source_files": "|".join(sorted(sources)),
                "usage_count": major_alias_usage[(major_name, code, system)],
                "ambiguity_status": ambiguity_status,
                "evidence_id": stable_hash("major_code_alias", major_name, code, system, ambiguity_status),
            }
        )

    programs: list[dict[str, Any]] = []
    admission_history: list[dict[str, Any]] = []
    plan_history: list[dict[str, Any]] = []
    evidence: dict[str, dict[str, Any]] = {}
    seen_programs: set[str] = set()

    def add_evidence(evidence_id: str, source_file: str, quality: str = "A", payload: Any = "") -> None:
        evidence[evidence_id] = {
            "evidence_id": evidence_id,
            "source_file": source_file,
            "quality_level": quality,
            "source_url": "",
            "payload_hash": stable_hash(payload),
        }

    def source_evidence_id(source_file: str, quality: str = "A") -> str:
        evidence_id = stable_hash("source", source_file, quality)
        add_evidence(evidence_id, source_file, quality, source_file)
        return evidence_id

    def make_program_id(row: dict[str, Any]) -> str:
        school_name = normalize_name(row.get("school_name"))
        major_name = normalize_name(row.get("major_name"))
        year = int(row.get("year") or 0)
        round_num = int(row.get("round") or 0)
        batch = str(row.get("batch") or "常规批")
        level = str(row.get("level") or ("本科" if round_num == 1 else ""))
        return stable_hash(
            level,
            year,
            round_num,
            batch,
            row.get("school_code", ""),
            row.get("major_code", ""),
            school_name,
            major_name,
        )

    def add_program(row: dict[str, Any], *, source_quality: str = "A") -> str:
        school_name = normalize_name(row.get("school_name"))
        major_name = normalize_name(row.get("major_name"))
        year = int(row.get("year") or 0)
        round_num = int(row.get("round") or 0)
        batch = str(row.get("batch") or "常规批")
        level = str(row.get("level") or ("本科" if round_num == 1 else ""))
        program_id = make_program_id(row)
        if program_id in seen_programs:
            return program_id
        seen_programs.add(program_id)
        evidence_id = stable_hash("program", program_id, row.get("source_file", ""))
        programs.append(
            {
                "program_id": program_id,
                "school_id": school_id_by_name.get(school_name, stable_hash("school", school_name)),
                "major_id": major_id_by_name.get(major_name, stable_hash("major", major_name)),
                "school_code": str(row.get("school_code", "")).strip(),
                "major_code": str(row.get("major_code", "")).strip(),
                "school_name": school_name,
                "major_name": major_name,
                "level": level,
                "year": year,
                "round": round_num,
                "batch": batch,
                "category": str(row.get("category") or "普通类"),
                "plan_count": row.get("plan_count"),
                "min_rank": row.get("min_rank"),
                "subject_check_status": "REVIEW",
                "region_check_status": "REVIEW",
                "source_quality": source_quality,
                "source_file": str(row.get("source_file", "")),
                "evidence_id": evidence_id,
            }
        )
        add_evidence(evidence_id, str(row.get("source_file", "")), source_quality, row)
        return program_id

    for row in admission_rows:
        if int(row.get("year") or 0) == latest_program_year:
            program_id = add_program(row)
        else:
            program_id = make_program_id(row)
        evidence_id = source_evidence_id(str(row.get("source_file", "")), "A")
        admission_history.append(
            {
                "program_id": program_id,
                "year": int(row.get("year") or 0),
                "round": int(row.get("round") or 0),
                "school_code": str(row.get("school_code", "")).strip(),
                "major_code": str(row.get("major_code", "")).strip(),
                "plan_count": row.get("plan_count"),
                "min_rank": row.get("min_rank"),
                "source_file": str(row.get("source_file", "")),
                "evidence_id": evidence_id,
            }
        )
        add_evidence(evidence_id, str(row.get("source_file", "")), "A", row)

    for row in plan_rows:
        if int(row.get("year") or 0) == latest_program_year:
            program_id = add_program(row)
        else:
            program_id = make_program_id(row)
        evidence_id = source_evidence_id(str(row.get("source_file", "")), "A")
        plan_history.append(
            {
                "program_id": program_id,
                "year": int(row.get("year") or 0),
                "batch": str(row.get("batch") or ""),
                "category": str(row.get("category") or ""),
                "school_code": str(row.get("school_code", "")).strip(),
                "major_code": str(row.get("major_code", "")).strip(),
                "plan_count": row.get("plan_count"),
                "source_file": str(row.get("source_file", "")),
                "evidence_id": evidence_id,
            }
        )

    with sqlite3.connect(str(tmp_path)) as conn:
        create_master_schema(conn)
        conn.executemany(
            """
            INSERT INTO schools VALUES (
                :school_id,:school_name,:normalized_name,:subject_school_codes,
                :admission_school_codes,:province,:city,:city_status,
                :school_level_tag,:ownership_tag,:subject_school_code_count,
                :admission_school_code_count,:program_count,:code_status,
                :source_files,:evidence_id
            )
            """,
            schools,
        )
        conn.executemany(
            """
            INSERT INTO school_code_aliases VALUES (
                :alias_id,:school_id,:school_name,:school_code,:code_system,
                :source_files,:usage_count,:ambiguity_status,:evidence_id
            )
            """,
            school_code_aliases,
        )
        conn.executemany(
            """
            INSERT INTO majors VALUES (
                :major_id,:major_name,:normalized_name,:major_code_samples,
                :major_family,:is_teacher,:is_law,:is_english,:is_finance,
                :is_bio_related,:preference_tags,:classification_status,
                :major_code_count,:program_count,:code_status,:source_files,:evidence_id
            )
            """,
            majors,
        )
        conn.executemany(
            """
            INSERT INTO major_code_aliases VALUES (
                :alias_id,:major_id,:major_name,:major_code,:code_system,
                :source_files,:usage_count,:ambiguity_status,:evidence_id
            )
            """,
            major_code_aliases,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO programs VALUES (:program_id,:school_id,:major_id,:school_code,:major_code,:school_name,:major_name,:level,:year,:round,:batch,:category,:plan_count,:min_rank,:subject_check_status,:region_check_status,:source_quality,:source_file,:evidence_id)",
            programs,
        )
        conn.executemany(
            "INSERT INTO admission_history VALUES (:program_id,:year,:round,:school_code,:major_code,:plan_count,:min_rank,:source_file,:evidence_id)",
            admission_history,
        )
        conn.executemany(
            "INSERT INTO plan_history VALUES (:program_id,:year,:batch,:category,:school_code,:major_code,:plan_count,:source_file,:evidence_id)",
            plan_history,
        )
        conn.executemany(
            "INSERT OR REPLACE INTO evidence VALUES (:evidence_id,:source_file,:quality_level,:source_url,:payload_hash)",
            list(evidence.values()),
        )
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "schools",
                "school_code_aliases",
                "majors",
                "major_code_aliases",
                "programs",
                "admission_history",
                "plan_history",
                "evidence",
            )
        }
        conn.execute("PRAGMA optimize")

    tmp_path.replace(db_path)
    meta = {
        "dataset": "master SQLite 主索引",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "db_file": rel(db_path),
        "counts": counts,
        "source_files": {
            "subject": [rel(path) for _, _, path in subject_index.source_files()],
            "region": rel(region_index.DEFAULT_REGION_DB_PATH),
            "admission": "processed/投档表/20??_round*.json",
            "plans": "processed/志愿计划/20??.json",
        },
        "program_id_formula": "sha256(level|year|round|batch|school_code|major_code|school_name|major_name)",
        "code_alias_policy": {
            "school_code_aliases": "按院校名称、院校代码、代码体系聚合；同一代码体系下同码多校为 REVIEW。",
            "major_code_aliases": "专业代码不是全局唯一，仅保留最近招生年份的专业代码别名；正式判断必须结合 program_id 或学校+专业组合。",
            "major_code_samples": "专业主表仅保存前 30 个代码样本，完整当前代码看 major_code_aliases，历史明细看 admission_history/plan_history。",
        },
        "hard_gate_policy": "正式候选必须有 program_id/evidence_id/source_file；REVIEW 不得口头放行。",
    }
    write_json(meta_path, meta)
    return meta
