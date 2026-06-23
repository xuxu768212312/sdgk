#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the deterministic SQLite index for subject requirements."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from subject_eligibility import (
    DEFAULT_DB_PATH,
    DEFAULT_META_PATH,
    create_schema,
    iter_source_rows,
    make_evidence_id,
    rel,
    source_files,
    validate_requirement_row,
)


def build_index(db_path: Path, meta_path: Path, rebuild: bool) -> Dict[str, Any]:
    if db_path.exists() and not rebuild:
        raise FileExistsError(f"{rel(db_path)} already exists; pass --rebuild to replace it")

    tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    validation_errors: List[str] = []
    records: List[Dict[str, Any]] = []
    source_counts: Dict[str, int] = {}

    for row, source_path in iter_source_rows():
        errors = validate_requirement_row(row, source_path)
        if errors:
            validation_errors.extend(errors)
            if len(validation_errors) >= 20:
                break
        record = {
            "evidence_id": make_evidence_id(row),
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
    with sqlite3.connect(str(tmp_path)) as conn:
        create_schema(conn)
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
        "source_files": [rel(path) for _, _, path in source_files()],
        "publisher": "山东省教育招生考试院",
        "official_domain": "sdzk.cn",
        "quality_level": "A",
        "verification_status": "derived_from_processed_subject_requirements",
        "evidence_id_formula": "sha256(edition|level|school_code|major_code|major_name|subject_requirement_raw)",
        "hard_gate_policy": "志愿方案中任何 BLOCK 或 REVIEW 均不得作为正式交付方案。",
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Build subject requirement SQLite index.")
    parser.add_argument("--rebuild", action="store_true", help="Replace an existing index.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite output path.")
    parser.add_argument("--meta", type=Path, default=DEFAULT_META_PATH, help="Metadata JSON output path.")
    args = parser.parse_args()

    try:
        meta = build_index(args.db, args.meta, args.rebuild)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"OK: built {meta['db_file']}")
    print(f"rows: {meta['row_count']}")
    print(f"meta: {rel(args.meta)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
