from __future__ import annotations

from pathlib import Path
from typing import Any

from sdgk.core.io import read_json
from sdgk.core.paths import PROCESSED_DIR


SCORE_TABLE_DIR = PROCESSED_DIR / "一分一段表"


def available_years(data_dir: Path = SCORE_TABLE_DIR) -> list[int]:
    years: list[int] = []
    for path in data_dir.glob("20??.json"):
        try:
            years.append(int(path.stem))
        except ValueError:
            continue
    return sorted(years)


def reference_year(year: int, data_dir: Path = SCORE_TABLE_DIR) -> int | None:
    candidates = [item for item in available_years(data_dir) if item <= year]
    if candidates:
        return max(candidates)
    years = available_years(data_dir)
    return max(years) if years else None


def load_score_table(year: int, data_dir: Path = SCORE_TABLE_DIR) -> list[dict[str, Any]]:
    path = data_dir / f"{year}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{path} is not a JSON list")
    return [dict(row) for row in payload]


def rank_for_score(score: int | float, year: int, data_dir: Path = SCORE_TABLE_DIR) -> dict[str, Any]:
    ref_year = reference_year(year, data_dir)
    if ref_year is None:
        return {
            "rank": None,
            "reference_year": None,
            "simulation": True,
            "reason_code": "SCORE_TABLE_MISSING",
        }

    rows = load_score_table(ref_year, data_dir)
    numeric_score = float(score)
    exact = [row for row in rows if float(row.get("score") or -1) == numeric_score]
    if exact:
        rank = exact[0].get("total_cumulative")
    else:
        lower_or_equal = [row for row in rows if float(row.get("score") or -1) <= numeric_score]
        if lower_or_equal:
            best = max(lower_or_equal, key=lambda row: float(row.get("score") or -1))
            rank = best.get("total_cumulative")
        else:
            rank = None

    return {
        "rank": int(rank) if rank is not None else None,
        "reference_year": ref_year,
        "simulation": ref_year != year,
        "reason_code": "OK" if rank is not None else "SCORE_OUT_OF_TABLE",
    }
