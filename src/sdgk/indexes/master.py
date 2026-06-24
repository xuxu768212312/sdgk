from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sdgk.indexes.builders import DEFAULT_MASTER_DB_PATH

MASTER_TABLES = (
    "schools",
    "school_code_aliases",
    "majors",
    "major_code_aliases",
    "programs",
    "admission_history",
    "plan_history",
    "evidence",
)


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
        for table in MASTER_TABLES:
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


def school_code_aliases(
    *,
    school_id: str = "",
    school_code: str = "",
    limit: int = 50,
    db_path: Path = DEFAULT_MASTER_DB_PATH,
) -> list[dict[str, Any]]:
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM school_code_aliases
            WHERE (? = '' OR school_id = ?)
              AND (? = '' OR school_code = ?)
            ORDER BY ambiguity_status DESC, code_system, school_code, school_name
            LIMIT ?
            """,
            (school_id, school_id, school_code.strip().upper(), school_code.strip().upper(), limit),
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


def major_code_aliases(
    *,
    major_id: str = "",
    major_code: str = "",
    limit: int = 50,
    db_path: Path = DEFAULT_MASTER_DB_PATH,
) -> list[dict[str, Any]]:
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM major_code_aliases
            WHERE (? = '' OR major_id = ?)
              AND (? = '' OR major_code = ?)
            ORDER BY ambiguity_status DESC, code_system, major_code, major_name
            LIMIT ?
            """,
            (major_id, major_id, major_code.strip().upper(), major_code.strip().upper(), limit),
        ).fetchall()
    return [row_dict(row) for row in rows]


PROGRAM_SELECT = """
    SELECT p.*, s.province, s.city, s.city_status, s.school_level_tag,
           s.code_status AS school_code_status,
           m.major_family, m.preference_tags, m.classification_status AS major_classification_status,
           m.major_code_count, m.code_status AS major_code_status,
           m.is_teacher, m.is_law, m.is_english, m.is_finance, m.is_bio_related
    FROM programs p
    LEFT JOIN schools s ON p.school_id = s.school_id
    LEFT JOIN majors m ON p.major_id = m.major_id
"""


def search_programs(
    query: str = "",
    *,
    school_name: str = "",
    major_name: str = "",
    school_code: str = "",
    major_code: str = "",
    year: int | None = None,
    limit: int = 50,
    db_path: Path = DEFAULT_MASTER_DB_PATH,
) -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    school_like = f"%{school_name.strip()}%"
    major_like = f"%{major_name.strip()}%"
    normalized_school_code = school_code.strip().upper()
    normalized_major_code = major_code.strip().upper()
    with connect_master(db_path) as conn:
        rows = conn.execute(
            f"""
            {PROGRAM_SELECT}
            WHERE p.year = COALESCE(?, (SELECT MAX(year) FROM programs))
              AND (? = '%%' OR p.school_name LIKE ? OR p.major_name LIKE ? OR p.school_code LIKE ? OR p.major_code LIKE ?)
              AND (? = '%%' OR p.school_name LIKE ?)
              AND (? = '%%' OR p.major_name LIKE ?)
              AND (? = '' OR UPPER(p.school_code) = ?)
              AND (? = '' OR UPPER(p.major_code) = ?)
            ORDER BY p.min_rank IS NULL, p.min_rank ASC, p.school_name, p.major_name
            LIMIT ?
            """,
            (
                year,
                like,
                like,
                like,
                like,
                like,
                school_like,
                school_like,
                major_like,
                major_like,
                normalized_school_code,
                normalized_school_code,
                normalized_major_code,
                normalized_major_code,
                limit,
            ),
        ).fetchall()
    return [row_dict(row) for row in rows]


def recent_programs(limit: int = 200, db_path: Path = DEFAULT_MASTER_DB_PATH) -> list[dict[str, Any]]:
    with connect_master(db_path) as conn:
        rows = conn.execute(
            """
            """ + PROGRAM_SELECT + """
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
            """ + PROGRAM_SELECT + """
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
