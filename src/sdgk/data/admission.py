from __future__ import annotations

from pathlib import Path
from typing import Any

from sdgk.core.io import read_json
from sdgk.core.paths import PROCESSED_DIR


ADMISSION_DIR = PROCESSED_DIR / "投档表"


def load_admission_rows(year: int | None = None, round_num: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = f"{year}_round*.json" if year else "20??_round*.json"
    for path in sorted(ADMISSION_DIR.glob(pattern)):
        if round_num is not None and f"_round{round_num}" not in path.name:
            continue
        payload = read_json(path)
        if not isinstance(payload, list):
            continue
        for row in payload:
            copied = dict(row)
            copied["source_file"] = str(path)
            rows.append(copied)
    return rows
