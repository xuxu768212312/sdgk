#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Risk-aware volunteer strategy optimizer.

Input candidates are expected to be pre-built from official processed data.
This optimizer enforces source-quality and subject hard gates before ranking.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


ALGORITHM_VERSION = "strategy_optimizer_v4_rush_guard_fail_closed"
QUALITY_SCORE = {"S": 1.0, "A": 0.95, "B": 0.85, "C": 0.45, "D": 0.0}
FORMAL_QUALITY = {"S", "A", "B"}

TIER_VALUE = {
    "C9": 1.0,
    "985": 0.95,
    "211": 0.88,
    "双一流": 0.86,
    "省重点": 0.70,
    "公办本科": 0.62,
    "独立学院": 0.34,
    "民办本科": 0.30,
    "职业本科": 0.24,
}

BASE_PROFILES = {
    "conservative": {
        "risk_aversion": 1.35,
        "targets": {"冲": 14, "稳": 38, "保": 34, "垫": 10},
        "mins": {"冲": 0, "稳": 28, "保": 28, "垫": 8},
        "maxs": {"冲": 18, "稳": 44, "保": 42, "垫": 16},
        "max_conservative_slip": 0.01,
        "min_rush_probability": 0.20,
        "deep_rush_probability": 0.20,
        "max_deep_rush": 0,
        "min_deep_rush_value_capture": 0.70,
    },
    "standard": {
        "risk_aversion": 1.0,
        "targets": {"冲": 24, "稳": 40, "保": 26, "垫": 6},
        "mins": {"冲": 12, "稳": 30, "保": 20, "垫": 6},
        "maxs": {"冲": 28, "稳": 46, "保": 34, "垫": 12},
        "max_conservative_slip": 0.03,
        "min_rush_probability": 0.15,
        "deep_rush_probability": 0.20,
        "max_deep_rush": 4,
        "min_deep_rush_value_capture": 0.68,
    },
    "aggressive": {
        "risk_aversion": 0.75,
        "targets": {"冲": 30, "稳": 38, "保": 22, "垫": 6},
        "mins": {"冲": 18, "稳": 28, "保": 16, "垫": 4},
        "maxs": {"冲": 36, "稳": 44, "保": 30, "垫": 10},
        "max_conservative_slip": 0.05,
        "min_rush_probability": 0.12,
        "deep_rush_probability": 0.20,
        "max_deep_rush": 8,
        "min_deep_rush_value_capture": 0.65,
    },
    "opportunistic": {
        "risk_aversion": 0.65,
        "targets": {"冲": 34, "稳": 36, "保": 20, "垫": 6},
        "mins": {"冲": 22, "稳": 26, "保": 16, "垫": 4},
        "maxs": {"冲": 40, "稳": 42, "保": 30, "垫": 10},
        "max_conservative_slip": 0.06,
        "min_rush_probability": 0.10,
        "deep_rush_probability": 0.20,
        "max_deep_rush": 10,
        "min_deep_rush_value_capture": 0.65,
    },
}


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        return default


def normalize_probability(value: Any) -> Optional[float]:
    p = to_float(value)
    if p is None:
        return None
    if not math.isfinite(p):
        return None
    if p > 1:
        p = p / 100.0
    if p < 0 or p > 1:
        return None
    return p


def normalize_unit(value: Any, default: Optional[float] = None) -> Optional[float]:
    x = to_float(value, default)
    if x is None:
        return default
    if not math.isfinite(x):
        return None
    if x > 1:
        x = x / 100.0
    if x < 0 or x > 1:
        return None
    return x


def text(row: Dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        if key in row and row[key] is not None and str(row[key]).strip() != "":
            return str(row[key]).strip()
    return default


def candidate_probability(row: Dict[str, Any]) -> Optional[float]:
    for key in ("probability", "admission_probability", "录取概率", "p"):
        if key in row:
            return normalize_probability(row[key])
    return None


def candidate_utility(row: Dict[str, Any]) -> Optional[float]:
    for key in ("utility", "utility_score", "效用分", "满意度"):
        if key in row:
            return normalize_unit(row[key])
    return None


def candidate_rsi(row: Dict[str, Any]) -> Optional[float]:
    for key in ("rsi", "rank_stability", "位次稳定性", "稳定性"):
        if key in row:
            return normalize_unit(row[key])
    return 0.75


def candidate_optional_unit(row: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            value = normalize_unit(row[key])
            return default if value is None else value
    return default


def candidate_school_tier_value(row: Dict[str, Any]) -> float:
    explicit = candidate_optional_unit(row, "school_value", "school_quality", "university_score", "院校价值", default=-1.0)
    if explicit >= 0:
        return explicit

    tier_text = text(row, "school_tier", "institution_tier", "院校层次", "学校层次", default="")
    for key, value in TIER_VALUE.items():
        if key in tier_text:
            return value

    school_name = text(row, "school_name", "院校名称", "学校名称", default="")
    if "职业技术大学" in school_name or "职业大学" in school_name:
        return TIER_VALUE["职业本科"]
    if "学院" in school_name or "大学" in school_name:
        return 0.45
    return 0.0


def candidate_value_capture(row: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Score low-rank opportunity without weakening hard safety gates.

    The score highlights candidates where a lower rank may still buy stronger
    school/major/preference value. It is optional: missing fields produce a
    conservative low score, never fabricated defaults.
    """

    school_value = candidate_school_tier_value(row)
    major_value = candidate_optional_unit(row, "major_value", "major_quality", "专业价值", "专业强度")
    preference_fit = candidate_optional_unit(row, "preference_fit", "major_preference", "偏好匹配", "兴趣匹配")
    location_fit = candidate_optional_unit(row, "location_fit", "city_fit", "region_fit", "地域匹配")
    opportunity = candidate_optional_unit(
        row,
        "value_opportunity",
        "rank_value_gap",
        "低分机会",
        "位次性价比",
    )
    affordability = candidate_optional_unit(row, "affordability", "cost_fit", "学费适配", default=0.5)
    plan_stability = candidate_optional_unit(row, "plan_stability", "plan_confidence", "计划稳定性", default=0.5)

    score = (
        0.28 * school_value
        + 0.24 * major_value
        + 0.18 * preference_fit
        + 0.12 * location_fit
        + 0.12 * opportunity
        + 0.03 * affordability
        + 0.03 * plan_stability
    )
    reasons: List[str] = []
    if school_value >= 0.7:
        reasons.append("HIGH_SCHOOL_VALUE")
    if major_value >= 0.75:
        reasons.append("HIGH_MAJOR_VALUE")
    if opportunity >= 0.7:
        reasons.append("LOW_RANK_VALUE_GAP")
    if preference_fit >= 0.75:
        reasons.append("HIGH_PREFERENCE_FIT")
    if affordability < 0.35:
        reasons.append("AFFORDABILITY_RISK")
    return round(max(0.0, min(1.0, score)), 6), reasons


def candidate_quality(row: Dict[str, Any]) -> str:
    value = text(row, "source_quality", "quality_level", "数据质量", default="D").upper()
    if value in QUALITY_SCORE:
        return value
    return "D"


def candidate_subject_status(row: Dict[str, Any]) -> str:
    return text(row, "subject_check_status", "选科审核状态", default="REVIEW").upper()


def candidate_source_file(row: Dict[str, Any]) -> str:
    return text(row, "source_file", "数据来源", "source_path", default="")


def candidate_key(row: Dict[str, Any]) -> Optional[str]:
    school_code = text(row, "school_code", "院校代码", "学校代码", default="")
    major_code = text(row, "major_code", "专业代码", default="")
    if school_code and major_code:
        return f"code:{school_code}|{major_code}"
    school_name = text(row, "school_name", "院校名称", "学校名称", default="")
    major_name = text(row, "major_name", "专业名称", default="")
    if school_name and major_name:
        return f"name:{school_name}|{major_name}"
    return None


def classify_bucket(probability: float, min_rush_probability: float = 0.15) -> str:
    if probability >= 0.98:
        return "垫"
    if probability >= 0.88:
        return "保"
    if probability >= 0.60:
        return "稳"
    if probability >= min_rush_probability:
        return "冲"
    return "弃"


def rush_tier(probability: float, bucket: str, deep_rush_probability: float) -> str:
    if bucket != "冲":
        return ""
    if probability < deep_rush_probability:
        return "deep_rush"
    return "rush"


def scaled_profile(profile_name: str, slots: int) -> Dict[str, Any]:
    base = BASE_PROFILES[profile_name]
    factor = slots / 96.0
    scaled: Dict[str, Any] = {
        "risk_aversion": base["risk_aversion"],
        "max_conservative_slip": base["max_conservative_slip"],
        "min_rush_probability": base["min_rush_probability"],
        "deep_rush_probability": base["deep_rush_probability"],
        "min_deep_rush_value_capture": base["min_deep_rush_value_capture"],
        "max_deep_rush": max(0, int(round(base["max_deep_rush"] * factor))),
        "targets": {},
        "mins": {},
        "maxs": {},
    }
    for field in ("targets", "mins", "maxs"):
        for bucket, value in base[field].items():
            scaled[field][bucket] = max(0, int(round(value * factor)))
    if slots > 0:
        scaled["mins"]["垫"] = max(1, scaled["mins"]["垫"])
    total_targets = sum(scaled["targets"].values())
    while total_targets < slots:
        scaled["targets"]["稳"] += 1
        total_targets += 1
    while total_targets > slots and scaled["targets"]["冲"] > 0:
        scaled["targets"]["冲"] -= 1
        total_targets -= 1
    return scaled


def duplicate_candidate_keys(candidates: Iterable[Dict[str, Any]]) -> Set[str]:
    counts: Counter = Counter()
    for row in candidates:
        key = candidate_key(row)
        if key:
            counts[key] += 1
    return {key for key, count in counts.items() if count > 1}


def gate_candidate(row: Dict[str, Any], duplicate_keys: Set[str]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    p = candidate_probability(row)
    if p is None:
        reasons.append("MISSING_OR_INVALID_PROBABILITY")
    utility = candidate_utility(row)
    if utility is None:
        reasons.append("MISSING_OR_INVALID_UTILITY")
    rsi = candidate_rsi(row)
    if rsi is None:
        reasons.append("INVALID_RSI")
    quality = candidate_quality(row)
    if quality not in FORMAL_QUALITY:
        reasons.append("SOURCE_QUALITY_NOT_FORMAL")
    subject_status = candidate_subject_status(row)
    if subject_status != "PASS":
        reasons.append("SUBJECT_NOT_PASS")
    if text(row, "evidence_id", "选科证据ID", default="") == "":
        reasons.append("MISSING_SUBJECT_EVIDENCE_ID")
    if not candidate_source_file(row):
        reasons.append("MISSING_SOURCE_FILE")
    key = candidate_key(row)
    if not key:
        reasons.append("MISSING_CANDIDATE_KEY")
    elif key in duplicate_keys:
        reasons.append("DUPLICATE_CANDIDATE_KEY")
    return len(reasons) == 0, reasons


def score_candidate(
    row: Dict[str, Any],
    risk_aversion: float,
    min_rush_probability: float = 0.15,
    deep_rush_probability: float = 0.20,
) -> Dict[str, Any]:
    p = candidate_probability(row)
    if p is None:
        raise ValueError("candidate probability is required after gating")
    utility = candidate_utility(row)
    rsi = candidate_rsi(row)
    if utility is None or rsi is None:
        raise ValueError("candidate utility and rsi are required after gating")
    quality = candidate_quality(row)
    q_score = QUALITY_SCORE[quality]
    bucket = classify_bucket(p, min_rush_probability=min_rush_probability)
    value_capture_score, value_reasons = candidate_value_capture(row)
    tier = rush_tier(p, bucket, deep_rush_probability)
    tail_penalty = risk_aversion * (1.0 - p) * (1.0 - rsi)
    affordability_risk = max(0.0, 0.35 - candidate_optional_unit(row, "affordability", "cost_fit", "学费适配", default=0.5))
    score = (
        0.38 * utility
        + 0.23 * p
        + 0.10 * rsi
        + 0.07 * q_score
        + 0.22 * value_capture_score
        - tail_penalty
        - 0.08 * affordability_risk
    )
    enriched = dict(row)
    enriched.update(
        {
            "probability": round(p, 6),
            "utility": round(utility, 6),
            "rsi": round(rsi, 6),
            "source_quality": quality,
            "gradient_bucket": bucket,
            "rush_tier": tier,
            "rush_probability_floor": min_rush_probability,
            "deep_rush_probability": deep_rush_probability,
            "value_capture_score": value_capture_score,
            "value_capture_reasons": value_reasons,
            "strategy_score": round(score, 6),
            "tail_penalty": round(tail_penalty, 6),
            "affordability_risk": round(affordability_risk, 6),
        }
    )
    return enriched


def independent_slip_probability(selected: Iterable[Dict[str, Any]]) -> float:
    log_prob = 0.0
    for row in selected:
        p = normalize_probability(row.get("probability")) or 0.0
        if p >= 1:
            return 0.0
        log_prob += math.log1p(-p)
    return round(math.exp(log_prob), 12)


def conservative_slip_probability(selected: Iterable[Dict[str, Any]]) -> float:
    """Fail-closed baseline that does not assume volunteer independence.

    Volunteer outcomes are often highly correlated by rank. The independent
    product can be unrealistically optimistic, so the hard gate also checks the
    failure probability of the strongest single selected safety option.
    """

    probabilities = [normalize_probability(row.get("probability")) or 0.0 for row in selected]
    if not probabilities:
        return 1.0
    return round(1.0 - max(probabilities), 12)


def concentration_warnings(selected: Iterable[Dict[str, Any]], slots: int) -> List[str]:
    warnings: List[str] = []
    school_counts: Counter = Counter()
    for row in selected:
        school = text(row, "school_code", "院校代码", default="") or text(row, "school_name", "院校名称", default="")
        if school:
            school_counts[school] += 1
    max_same_school = max(8, int(math.ceil(slots * 0.18)))
    for school, count in school_counts.items():
        if count > max_same_school:
            warnings.append(f"HIGH_SAME_SCHOOL_CONCENTRATION:{school}:{count}>{max_same_school}")
    return warnings


def candidate_sort_key(row: Dict[str, Any]) -> Tuple[float, float, float, float, int]:
    return (
        -float(row["strategy_score"]),
        -float(row.get("value_capture_score", 0.0)),
        -float(row["utility"]),
        -float(row["probability"]),
        int(row.get("input_index", 0)),
    )


def rush_cap_reason(row: Dict[str, Any], selected: Iterable[Dict[str, Any]], profile: Dict[str, Any]) -> Optional[str]:
    if row.get("rush_tier") != "deep_rush":
        return None
    current = sum(1 for item in selected if item.get("rush_tier") == "deep_rush")
    cap = int(profile.get("max_deep_rush", 0))
    if current >= cap:
        return f"DEEP_RUSH_OVER_PROFILE_CAP: expected <= {cap}"
    return None


def rush_metrics(selected: Iterable[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    selected_list = list(selected)
    rush_rows = [row for row in selected_list if row.get("gradient_bucket") == "冲"]
    deep_rows = [row for row in selected_list if row.get("rush_tier") == "deep_rush"]
    probabilities = [float(row.get("probability", 0.0)) for row in rush_rows]
    return {
        "rush_count": len(rush_rows),
        "deep_rush_count": len(deep_rows),
        "ordinary_rush_count": len(rush_rows) - len(deep_rows),
        "min_selected_rush_probability": round(min(probabilities), 6) if probabilities else None,
        "rush_probability_floor": profile["min_rush_probability"],
        "deep_rush_probability": profile["deep_rush_probability"],
        "deep_rush_cap": profile["max_deep_rush"],
        "min_deep_rush_value_capture": profile["min_deep_rush_value_capture"],
    }


def rush_warnings(metrics: Dict[str, Any], risk_profile: str) -> List[str]:
    warnings: List[str] = []
    if metrics["rush_count"]:
        warnings.append(
            "RUSH_SELECTED: "
            f"profile={risk_profile}, count={metrics['rush_count']}, "
            f"min_probability={metrics['min_selected_rush_probability']}"
        )
    if metrics["deep_rush_count"]:
        warnings.append(
            "DEEP_RUSH_SELECTED: "
            f"{metrics['deep_rush_count']}<={metrics['deep_rush_cap']}, "
            f"value_capture_floor={metrics['min_deep_rush_value_capture']}"
        )
    return warnings


def optimize_candidates(candidates: List[Dict[str, Any]], slots: int = 96, risk_profile: str = "standard") -> Dict[str, Any]:
    if risk_profile not in BASE_PROFILES:
        raise ValueError("risk_profile must be one of: " + ", ".join(sorted(BASE_PROFILES)))
    if slots <= 0:
        raise ValueError("slots must be positive")

    profile = scaled_profile(risk_profile, slots)
    duplicate_keys = duplicate_candidate_keys(candidates)
    blocked: List[Dict[str, Any]] = []
    eligible: List[Dict[str, Any]] = []

    for index, row in enumerate(candidates, start=1):
        ok, reasons = gate_candidate(row, duplicate_keys)
        if not ok:
            blocked_row = dict(row)
            blocked_row["blocked_reasons"] = reasons
            blocked_row["input_index"] = index
            blocked.append(blocked_row)
            continue
        scored = score_candidate(
            row,
            profile["risk_aversion"],
            min_rush_probability=profile["min_rush_probability"],
            deep_rush_probability=profile["deep_rush_probability"],
        )
        scored["input_index"] = index
        if scored["gradient_bucket"] == "弃":
            scored["blocked_reasons"] = ["PROBABILITY_TOO_LOW"]
            blocked.append(scored)
        elif (
            scored["rush_tier"] == "deep_rush"
            and scored["value_capture_score"] < profile["min_deep_rush_value_capture"]
        ):
            scored["blocked_reasons"] = [
                "LOW_PROBABILITY_WITHOUT_VALUE_CAPTURE: "
                f"expected >= {profile['min_deep_rush_value_capture']}, "
                f"got {scored['value_capture_score']}"
            ]
            blocked.append(scored)
        else:
            eligible.append(scored)

    by_bucket: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        by_bucket[row["gradient_bucket"]].append(row)
    for bucket_rows in by_bucket.values():
        bucket_rows.sort(key=candidate_sort_key)

    selected: List[Dict[str, Any]] = []
    selected_ids = set()
    risk_capped: List[Dict[str, Any]] = []
    risk_capped_ids = set()

    def try_select(row: Dict[str, Any]) -> bool:
        if len(selected) >= slots:
            return False
        reason = rush_cap_reason(row, selected, profile)
        if reason:
            row_id = id(row)
            if row_id not in risk_capped_ids:
                capped_row = dict(row)
                capped_row["blocked_reasons"] = [reason]
                risk_capped.append(capped_row)
                risk_capped_ids.add(row_id)
            return False
        selected.append(row)
        selected_ids.add(id(row))
        return True

    for bucket in ("冲", "稳", "保", "垫"):
        target = profile["targets"].get(bucket, 0)
        added = 0
        for row in by_bucket.get(bucket, []):
            if added >= target:
                break
            if try_select(row):
                added += 1

    leftovers = [row for row in eligible if id(row) not in selected_ids]
    leftovers.sort(key=candidate_sort_key)
    for row in leftovers:
        if len(selected) >= slots:
            break
        bucket = row["gradient_bucket"]
        current = sum(1 for item in selected if item["gradient_bucket"] == bucket)
        if current < profile["maxs"].get(bucket, slots):
            try_select(row)

    selected.sort(key=lambda x: (bucket_order(x["gradient_bucket"]), -x["strategy_score"], x.get("input_index", 0)))
    selected = selected[:slots]
    blocked.extend(risk_capped)

    counts = Counter(row["gradient_bucket"] for row in selected)
    rush_info = rush_metrics(selected, profile)
    violations: List[str] = []
    for bucket, min_count in profile["mins"].items():
        if counts.get(bucket, 0) < min_count:
            violations.append(f"INSUFFICIENT_{bucket}: expected >= {min_count}, got {counts.get(bucket, 0)}")
    if rush_info["deep_rush_count"] > profile["max_deep_rush"]:
        violations.append(
            "DEEP_RUSH_TOO_MANY: "
            f"expected <= {profile['max_deep_rush']}, got {rush_info['deep_rush_count']}"
        )
    if len(selected) < slots:
        violations.append(f"INSUFFICIENT_ELIGIBLE_CANDIDATES: expected {slots}, got {len(selected)}")
    conservative_slip = conservative_slip_probability(selected)
    if conservative_slip > profile["max_conservative_slip"]:
        violations.append(
            "CONSERVATIVE_SLIP_TOO_HIGH: "
            f"expected <= {profile['max_conservative_slip']}, got {conservative_slip}"
        )

    for order, row in enumerate(selected, start=1):
        row["strategy_order"] = order

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "hard_gate_passed": not violations,
        "risk_profile": risk_profile,
        "slots": slots,
        "input_count": len(candidates),
        "selected_count": len(selected),
        "blocked_count": len(blocked),
        "gradient_counts": dict(counts),
        "rush_counts": rush_info,
        "quota_profile": profile,
        "violations": violations,
        "warnings": concentration_warnings(selected, slots) + rush_warnings(rush_info, risk_profile),
        "independent_model_slip_probability": independent_slip_probability(selected),
        "conservative_slip_probability": conservative_slip,
        "selected": selected,
        "blocked": blocked,
    }


def bucket_order(bucket: str) -> int:
    return {"冲": 0, "稳": 1, "保": 2, "垫": 3}.get(bucket, 9)


def load_candidates(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        for key in ("candidates", "rows", "data"):
            if isinstance(payload, dict) and isinstance(payload.get(key), list):
                return [dict(row) for row in payload[key]]
        raise ValueError("JSON input must be a list or contain candidates/rows/data")
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize a volunteer candidate portfolio.")
    parser.add_argument("--input", required=True, type=Path, help="Candidate CSV/JSON.")
    parser.add_argument("--out", type=Path, help="Output JSON path.")
    parser.add_argument("--slots", type=int, default=96, help="Number of volunteers to select.")
    parser.add_argument("--risk-profile", choices=sorted(BASE_PROFILES), default="standard")
    args = parser.parse_args()

    try:
        candidates = load_candidates(args.input)
        result = optimize_candidates(candidates, slots=args.slots, risk_profile=args.risk_profile)
    except Exception as exc:
        error = {"hard_gate_passed": False, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False, indent=2))
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "algorithm_version",
                    "hard_gate_passed",
                    "selected_count",
                    "blocked_count",
                    "gradient_counts",
                    "rush_counts",
                    "conservative_slip_probability",
                    "violations",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["hard_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
