from __future__ import annotations

from pathlib import Path
from typing import Any

from sdgk.core.io import read_json
from sdgk.core.paths import PROCESSED_DIR


PLANS_DIR = PROCESSED_DIR / "志愿计划"


def load_plan_rows(year: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = f"{year}.json" if year else "20??.json"
    for path in sorted(PLANS_DIR.glob(pattern)):
        payload = read_json(path)
        if not isinstance(payload, list):
            continue
        for row in payload:
            copied = dict(row)
            copied["source_file"] = str(path)
            rows.append(copied)
    return rows
