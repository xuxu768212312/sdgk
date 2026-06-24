#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the deterministic school-region index."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from school_region import (
    DEFAULT_REGION_DB_PATH,
    DEFAULT_REGION_META_PATH,
    REGION_DIR,
    SUBJECT_SOURCE_FILES,
    build_school_records,
    create_schema,
    rel,
)


def build_index(db_path: Path, meta_path: Path, rebuild: bool) -> Dict[str, Any]:
    if db_path.exists() and not rebuild:
        raise FileExistsError(f"{rel(db_path)} already exists; pass --rebuild to replace it")
    REGION_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    records = build_school_records()
    with sqlite3.connect(str(tmp_path)) as conn:
        create_schema(conn)
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
        "source_files": [rel(path) for path in SUBJECT_SOURCE_FILES],
        "province_source": "processed/选科要求/*.json province 字段",
        "province_quality_level": "A",
        "city_policy": "城市仅在学校名显式地名或 reviewed override 时 PASS；多校区/不确定返回 REVIEW",
        "hard_gate_policy": "地区筛选不得使用 school_name contains 省名；省份必须查 province，城市不确定必须 REVIEW。",
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Build school region SQLite index.")
    parser.add_argument("--rebuild", action="store_true", help="Replace an existing index.")
    parser.add_argument("--db", type=Path, default=DEFAULT_REGION_DB_PATH)
    parser.add_argument("--meta", type=Path, default=DEFAULT_REGION_META_PATH)
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
