from __future__ import annotations

import math
from typing import Any


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def estimate_probability(student_rank: int | None, target_rank: int | None, rsi: float = 0.75) -> dict[str, Any]:
    if not student_rank or not target_rank or student_rank <= 0 or target_rank <= 0:
        return {
            "probability": None,
            "bucket": "REVIEW",
            "rsi": rsi,
            "evidence_strength": "missing_rank",
            "probability_reason_code": "MISSING_RANK",
        }
    ratio = student_rank / target_rank
    probability = logistic(8 * (1 - ratio)) * (0.85 + 0.15 * max(0.0, min(1.0, rsi)))
    probability = max(0.02, min(0.995, probability))
    if probability >= 0.98:
        bucket = "垫"
    elif probability >= 0.88:
        bucket = "保"
    elif probability >= 0.60:
        bucket = "稳"
    elif probability >= 0.10:
        bucket = "冲"
    else:
        bucket = "弃"
    return {
        "probability": round(probability, 6),
        "bucket": bucket,
        "rsi": round(rsi, 6),
        "evidence_strength": "rank_ratio",
        "probability_reason_code": "RANK_RATIO_LOGISTIC",
        "rank_ratio": round(ratio, 6),
    }


def rank_stability(ranks: list[int]) -> float:
    values = [rank for rank in ranks if rank and rank > 0]
    if len(values) < 2:
        return 0.65
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    if mean <= 0:
        return 0.65
    return max(0.0, min(1.0, 1 - (variance**0.5 / mean)))

