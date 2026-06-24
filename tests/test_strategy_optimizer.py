#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke tests for the strategy optimizer."""

from __future__ import annotations

from sdgk.strategy.optimizer import optimize_candidates, score_candidate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_candidate(index: int, probability: float, utility: float, bucket_hint: str = "") -> dict:
    return {
        "candidate_id": f"C{index:03d}",
        "school_name": f"测试大学{index}",
        "major_name": f"测试专业{index}",
        "school_code": f"T{index:04d}",
        "major_code": f"M{index:04d}",
        "probability": probability,
        "utility": utility,
        "rsi": 0.9,
        "source_quality": "A",
        "subject_check_status": "PASS",
        "evidence_id": f"evidence-{index}",
        "source_file": "processed/投档表/test.json",
        "bucket_hint": bucket_hint,
    }


def test_standard_optimizer() -> None:
    candidates = []
    for i in range(1, 9):
        candidates.append(make_candidate(i, 0.25 + i * 0.015, 0.80))
    for i in range(9, 25):
        candidates.append(make_candidate(i, 0.66 + (i % 4) * 0.03, 0.70 + (i % 5) * 0.03))
    for i in range(25, 41):
        candidates.append(make_candidate(i, 0.90 + (i % 4) * 0.015, 0.62 + (i % 5) * 0.03))
    for i in range(41, 49):
        candidates.append(make_candidate(i, 0.99, 0.55 + (i % 3) * 0.04))

    blocked_subject = make_candidate(60, 0.92, 0.95)
    blocked_subject["subject_check_status"] = "BLOCK"
    candidates.append(blocked_subject)

    blocked_quality = make_candidate(61, 0.99, 0.95)
    blocked_quality["source_quality"] = "D"
    candidates.append(blocked_quality)

    missing_evidence = make_candidate(62, 0.99, 0.95)
    missing_evidence["evidence_id"] = ""
    candidates.append(missing_evidence)

    invalid_probability = make_candidate(63, 150, 0.95)
    candidates.append(invalid_probability)

    duplicate_a = make_candidate(64, 0.99, 0.95)
    duplicate_b = make_candidate(65, 0.99, 0.95)
    duplicate_b["school_code"] = duplicate_a["school_code"]
    duplicate_b["major_code"] = duplicate_a["major_code"]
    candidates.extend([duplicate_a, duplicate_b])

    result = optimize_candidates(candidates, slots=24, risk_profile="standard")
    require(result["hard_gate_passed"], "balanced official candidates should pass")
    require(result["algorithm_version"] == "strategy_optimizer_v4_rush_guard_fail_closed", "algorithm version should be explicit")
    require(result["selected_count"] == 24, "should select requested slots")
    require(result["gradient_counts"].get("垫", 0) >= 2, "scaled profile should keep cushion volunteers")
    require(result["conservative_slip_probability"] <= 0.03, "standard profile should pass conservative slip gate")
    reasons = {reason for row in result["blocked"] for reason in row.get("blocked_reasons", [])}
    require("SUBJECT_NOT_PASS" in reasons, "subject BLOCK should be excluded")
    require("SOURCE_QUALITY_NOT_FORMAL" in reasons, "D-quality source should be excluded")
    require("MISSING_SUBJECT_EVIDENCE_ID" in reasons, "missing evidence id should be excluded")
    require("MISSING_OR_INVALID_PROBABILITY" in reasons, "invalid probability should be excluded")
    require("DUPLICATE_CANDIDATE_KEY" in reasons, "duplicate candidate key should be excluded")


def test_insufficient_cushion() -> None:
    candidates = [make_candidate(i, 0.7, 0.8) for i in range(1, 20)]
    result = optimize_candidates(candidates, slots=12, risk_profile="standard")
    require(not result["hard_gate_passed"], "plan without cushion volunteers should fail")
    require(any("INSUFFICIENT_垫" in v for v in result["violations"]), "must report insufficient cushion")


def test_conservative_slip_gate() -> None:
    candidates = []
    for i in range(1, 9):
        candidates.append(make_candidate(i, 0.35, 0.8))
    for i in range(9, 25):
        candidates.append(make_candidate(i, 0.68, 0.8))
    for i in range(25, 41):
        candidates.append(make_candidate(i, 0.9, 0.8))
    for i in range(41, 49):
        candidates.append(make_candidate(i, 0.965, 0.8))
    result = optimize_candidates(candidates, slots=24, risk_profile="standard")
    require(not result["hard_gate_passed"], "best safety below 97% should fail standard conservative slip gate")
    require(any("CONSERVATIVE_SLIP_TOO_HIGH" in v for v in result["violations"]), "must report conservative slip failure")


def test_value_capture_priority() -> None:
    baseline = make_candidate(1, 0.99, 0.7)
    baseline["school_tier"] = "民办本科"
    baseline["major_value"] = 0.45
    baseline["preference_fit"] = 0.45

    premium = make_candidate(2, 0.99, 0.7)
    premium["school_tier"] = "双一流"
    premium["major_value"] = 0.9
    premium["preference_fit"] = 0.9
    premium["value_opportunity"] = 0.95

    baseline_scored = score_candidate(baseline, risk_aversion=1.0)
    premium_scored = score_candidate(premium, risk_aversion=1.0)
    require(
        premium_scored["strategy_score"] > baseline_scored["strategy_score"],
        "value-capture candidate should score higher when safety and utility tie",
    )
    require(premium_scored["value_capture_score"] > baseline_scored["value_capture_score"], "value score should be exposed")
    require("LOW_RANK_VALUE_GAP" in premium_scored["value_capture_reasons"], "value-capture reasons should be explainable")


def add_high_value_fields(candidate: dict) -> dict:
    candidate["school_tier"] = "双一流"
    candidate["major_value"] = 0.95
    candidate["preference_fit"] = 0.90
    candidate["location_fit"] = 0.80
    candidate["value_opportunity"] = 0.95
    candidate["affordability"] = 0.80
    candidate["plan_stability"] = 0.80
    return candidate


def test_opportunistic_rush_profile() -> None:
    candidates = []
    for i in range(1, 5):
        candidates.append(add_high_value_fields(make_candidate(i, 0.11 + i * 0.015, 0.92)))
    for i in range(5, 15):
        candidates.append(make_candidate(i, 0.25 + (i % 4) * 0.03, 0.82))
    for i in range(15, 29):
        candidates.append(make_candidate(i, 0.66 + (i % 4) * 0.03, 0.78))
    for i in range(29, 43):
        candidates.append(make_candidate(i, 0.90 + (i % 4) * 0.015, 0.70))
    for i in range(43, 51):
        candidates.append(make_candidate(i, 0.99, 0.62))

    result = optimize_candidates(candidates, slots=24, risk_profile="opportunistic")
    require(result["hard_gate_passed"], "opportunistic profile should pass when safety buckets are sufficient")
    require(result["selected_count"] == 24, "opportunistic profile should fill all slots")
    require(result["rush_counts"]["deep_rush_count"] == 2, "scaled deep-rush cap should be enforced")
    require(result["rush_counts"]["min_selected_rush_probability"] < 0.20, "high-value deep rush can be selected")
    reasons = {reason for row in result["blocked"] for reason in row.get("blocked_reasons", [])}
    require(any(reason.startswith("DEEP_RUSH_OVER_PROFILE_CAP") for reason in reasons), "extra deep rush should be capped")


def test_deep_rush_requires_value_capture() -> None:
    weak_deep_rush = make_candidate(201, 0.11, 0.95)
    result = optimize_candidates([weak_deep_rush], slots=1, risk_profile="opportunistic")
    reasons = {reason for row in result["blocked"] for reason in row.get("blocked_reasons", [])}
    require(
        any(reason.startswith("LOW_PROBABILITY_WITHOUT_VALUE_CAPTURE") for reason in reasons),
        "deep rush below 20% needs high value-capture evidence",
    )

