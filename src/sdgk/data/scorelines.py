from __future__ import annotations

from typing import Any

from sdgk.core.io import read_json
from sdgk.core.paths import PROCESSED_DIR


SCORELINES_DIR = PROCESSED_DIR / "分数线"


def load_scorelines(year: int | None = None) -> dict[str, Any]:
    if year is not None:
        path = SCORELINES_DIR / f"{year}.json"
        if path.exists():
            payload = read_json(path)
            return dict(payload) if isinstance(payload, dict) else {"rows": payload}
    path = SCORELINES_DIR / "历史分数线_2020-2024.json"
    if path.exists():
        payload = read_json(path)
        return dict(payload) if isinstance(payload, dict) else {"rows": payload}
    return {}
