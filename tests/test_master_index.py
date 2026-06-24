from __future__ import annotations

import sqlite3

from sdgk.indexes.builders import DEFAULT_MASTER_DB_PATH
from sdgk.indexes.master import search_majors, search_schools, summary
from sdgk.indexes.region import DEFAULT_REGION_DB_PATH


def test_master_index_exists_and_counts() -> None:
    info = summary()
    assert info["exists"]
    assert info["counts"]["programs"] > 30000
    assert info["counts"]["admission_history"] > 150000
    assert info["counts"]["school_code_aliases"] > 2000
    assert info["counts"]["major_code_aliases"] > 20000


def test_region_schools_in_master() -> None:
    with sqlite3.connect(DEFAULT_REGION_DB_PATH) as region_conn, sqlite3.connect(DEFAULT_MASTER_DB_PATH) as master_conn:
        region_count = region_conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0]
        in_master = master_conn.execute(
            """
            SELECT COUNT(*)
            FROM schools
            WHERE province <> ''
            """
        ).fetchone()[0]
    assert in_master >= region_count


def test_search_school_uses_region_fields() -> None:
    rows = search_schools("青岛大学", limit=5)
    assert rows
    assert rows[0]["province"] == "山东"
    assert rows[0]["program_count"] > 0
    assert rows[0]["code_status"] in {"PASS", "REVIEW"}


def test_search_major_uses_tags_and_codes() -> None:
    rows = search_majors("法学", limit=10)
    assert rows
    assert any(row["major_family"] == "法学政法" for row in rows)
    assert any("法学" in row["preference_tags"] for row in rows)
    assert not any(row["major_name"] == "书法学" and row["major_family"] == "法学政法" for row in rows)
    assert all("major_code_count" in row for row in rows)


def test_code_alias_tables_are_queryable() -> None:
    with sqlite3.connect(DEFAULT_MASTER_DB_PATH) as conn:
        school_alias = conn.execute(
            """
            SELECT school_name, school_code, code_system, ambiguity_status
            FROM school_code_aliases
            WHERE school_name = '青岛大学'
            LIMIT 1
            """
        ).fetchone()
        major_alias = conn.execute(
            """
            SELECT major_name, major_code, code_system, ambiguity_status
            FROM major_code_aliases
            WHERE major_name LIKE '%法学%'
            LIMIT 1
            """
        ).fetchone()
    assert school_alias is not None
    assert school_alias[2] in {"subject_5_digit", "admission_school_code", "school_code_other"}
    assert major_alias is not None
    assert major_alias[2] in {"subject_major_code", "program_major_code", "major_code_other"}
