from __future__ import annotations

import sqlite3

from sdgk.indexes.builders import DEFAULT_MASTER_DB_PATH
from sdgk.indexes.master import search_schools, summary
from sdgk.indexes.region import DEFAULT_REGION_DB_PATH


def test_master_index_exists_and_counts() -> None:
    info = summary()
    assert info["exists"]
    assert info["counts"]["programs"] > 30000
    assert info["counts"]["admission_history"] > 150000


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
