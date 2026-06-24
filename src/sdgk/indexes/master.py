from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sdgk.indexes.builders import DEFAULT_MASTER_DB_PATH


def connect_master(db_path: Path = DEFAULT_MASTER_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def summary(db_path: Path = DEFAULT_MASTER_DB_PATH) -> dict[str, Any]:
    if not db_path.exists():
        return {"exists": False, "db_file": str(db_path), "counts": {}}
    with connect_master(db_path) as conn:
        counts = {}
        for table in ("schools", "majors", "programs", "admission_history", "plan_history", "evidence"):
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return {"exists": True, "db_file": str(db_path), "counts": counts}


def search_schools(query: str = "", limit: int = 20, db_path: Path = DEFAULT_MASTER_DB_PATH) -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM schools
            WHERE ? = '%%' OR school_name LIKE ? OR province LIKE ? OR city LIKE ?
            ORDER BY province, school_name
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
    return [row_dict(row) for row in rows]


def search_majors(
    query: str = "",
    family: str = "",
    limit: int = 20,
    db_path: Path = DEFAULT_MASTER_DB_PATH,
) -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM majors
            WHERE (? = '%%' OR major_name LIKE ?)
              AND (? = '' OR major_family = ?)
            ORDER BY classification_status, major_family, major_name
            LIMIT ?
            """,
            (like, like, family, family, limit),
        ).fetchall()
    return [row_dict(row) for row in rows]


def recent_programs(limit: int = 200, db_path: Path = DEFAULT_MASTER_DB_PATH) -> list[dict[str, Any]]:
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            SELECT p.*, s.province, s.city, s.city_status, m.major_family,
                   m.is_teacher, m.is_law, m.is_english, m.is_finance, m.is_bio_related
            FROM programs p
            LEFT JOIN schools s ON p.school_id = s.school_id
            LEFT JOIN majors m ON p.major_id = m.major_id
            WHERE p.year = (SELECT MAX(year) FROM programs)
            ORDER BY p.min_rank IS NULL, p.min_rank ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_dict(row) for row in rows]


def programs_for_rank(rank: int | None, limit: int = 1200, db_path: Path = DEFAULT_MASTER_DB_PATH) -> list[dict[str, Any]]:
    if rank is None:
        return recent_programs(limit=limit, db_path=db_path)
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            SELECT p.*, s.province, s.city, s.city_status, m.major_family,
                   m.is_teacher, m.is_law, m.is_english, m.is_finance, m.is_bio_related
            FROM programs p
            LEFT JOIN schools s ON p.school_id = s.school_id
            LEFT JOIN majors m ON p.major_id = m.major_id
            WHERE p.year = (SELECT MAX(year) FROM programs)
              AND p.min_rank IS NOT NULL
              AND p.min_rank BETWEEN ? AND ?
            ORDER BY CASE WHEN p.min_rank >= ? THEN 0 ELSE 1 END,
                     ABS(p.min_rank - ?) ASC,
                     p.min_rank DESC
            LIMIT ?
            """,
            (int(rank / 1.45), int(rank * 2.25), rank, rank, limit),
        ).fetchall()
    return [row_dict(row) for row in rows]
