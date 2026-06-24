from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sdgk.core.io import read_json, write_json
from sdgk.core.paths import ensure_students_path, rel
from sdgk.data.score_table import rank_for_score
from sdgk.indexes.master import programs_for_rank
from sdgk.indexes.region import check_school_regions
from sdgk.indexes.subject import check_eligibility, normalize_subjects
from sdgk.strategy.probability import estimate_probability


PREFERENCE_FIELDS = {
    "师范": ("is_teacher", "师范教育"),
    "法学": ("is_law", "法学政法"),
    "英语": ("is_english", "外语英语"),
    "金融": ("is_finance", "财经金融"),
    "生物工程": ("is_bio_related", "生物医农"),
    "生物": ("is_bio_related", "生物医农"),
}


def load_student_profile(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("student profile must be a JSON object")
    return payload


def student_subjects(profile: dict[str, Any]) -> list[str]:
    subjects = profile.get("subjects") or profile.get("选科") or profile.get("selected_subjects") or []
    normalized, invalid = normalize_subjects(subjects)
    if invalid or len(normalized) != 3:
        raise ValueError("student subjects must contain exactly 3 valid subjects")
    return normalized


def student_preferences(profile: dict[str, Any]) -> dict[str, Any]:
    regions = profile.get("regions") or profile.get("target_regions") or profile.get("地区偏好") or []
    if isinstance(regions, str):
        regions = [item.strip() for item in regions.replace("、", ",").split(",") if item.strip()]
    majors = profile.get("major_preferences") or profile.get("majors") or profile.get("专业偏好") or []
    if isinstance(majors, str):
        majors = [item.strip() for item in majors.replace("、", ",").split(",") if item.strip()]
    return {"regions": list(regions), "majors": list(majors)}


def resolve_rank(profile: dict[str, Any]) -> dict[str, Any]:
    year = int(profile.get("year") or profile.get("年份") or 2026)
    if profile.get("rank") or profile.get("位次"):
        return {
            "rank": int(profile.get("rank") or profile.get("位次")),
            "reference_year": year,
            "simulation": False,
            "reason_code": "PROFILE_RANK",
        }
    score = profile.get("score") or profile.get("分数")
    if score is None:
        return {
            "rank": None,
            "reference_year": None,
            "simulation": True,
            "reason_code": "MISSING_SCORE_OR_RANK",
        }
    return rank_for_score(float(score), year)


def major_preference_score(row: dict[str, Any], majors: list[str]) -> tuple[float, list[str]]:
    if not majors:
        return 0.5, []
    matched: list[str] = []
    score = 0.0
    major_name = str(row.get("major_name") or "")
    preference_tags = {item for item in str(row.get("preference_tags") or "").split("|") if item}
    for pref in majors:
        field_family = PREFERENCE_FIELDS.get(pref)
        if field_family:
            field, family = field_family
            if pref in preference_tags or int(row.get(field) or 0) == 1 or row.get("major_family") == family:
                matched.append(pref)
                score = max(score, 1.0)
        elif pref in preference_tags:
            matched.append(pref)
            score = max(score, 0.9)
        elif pref and pref in major_name:
            matched.append(pref)
            score = max(score, 0.55)
    if matched:
        return score, matched
    return 0.25, []


def location_score(region_status: str, regions: list[str]) -> float:
    if not regions:
        return 0.5
    if region_status == "MATCH":
        return 1.0
    if region_status == "REVIEW":
        return 0.35
    return 0.15


def build_candidate_pool(
    profile: dict[str, Any],
    *,
    limit: int = 4000,
    max_rows: int = 900,
    hard_region: bool = False,
) -> dict[str, Any]:
    year = int(profile.get("year") or profile.get("年份") or 2026)
    level = str(profile.get("level") or profile.get("批次") or "本科")
    subjects = student_subjects(profile)
    prefs = student_preferences(profile)
    rank_info = resolve_rank(profile)
    rank = rank_info.get("rank")

    rows = programs_for_rank(rank, limit=limit)
    candidates: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []

    for row in rows:
        if level and str(row.get("level") or "") not in {"", level, "本专科"}:
            continue
        min_rank = row.get("min_rank")
        if rank and min_rank:
            rank_ratio = float(rank) / float(min_rank)
            if rank_ratio > 1.35:
                continue

        subject = check_eligibility(
            year=year,
            level=level,
            subjects=subjects,
            school_code=str(row.get("school_code") or ""),
            major_code=str(row.get("major_code") or ""),
            school_name=str(row.get("school_name") or ""),
            major_name=str(row.get("major_name") or ""),
        )
        region = check_school_regions(
            prefs["regions"],
            school_name=str(row.get("school_name") or ""),
            subject_school_code="",
        ) if prefs["regions"] else {
            "status": "MATCH",
            "reason_code": "NO_REGION_LIMIT",
            "match_type": "not_required",
            "evidence_id": row.get("evidence_id"),
            "province": row.get("province") or "",
            "city": row.get("city") or "",
            "source_files": row.get("source_file") or "",
        }

        pref_score, matched_prefs = major_preference_score(row, prefs["majors"])
        reg_score = location_score(str(region.get("status")), prefs["regions"])
        probability_payload = estimate_probability(rank, min_rank)
        probability = probability_payload.get("probability")
        probability_value = float(probability) if probability is not None else 0.0
        utility = (
            0.38 * pref_score
            + 0.22 * reg_score
            + 0.18 * min(1.0, max(0.0, probability_value))
            + 0.12 * (0.70 if "大学" in str(row.get("school_name")) else 0.45)
            + 0.10 * (0.70 if int(row.get("plan_count") or 0) >= 5 else 0.45)
        )
        value_opportunity = 0.0
        if rank and min_rank:
            value_opportunity = max(0.0, min(1.0, 1.18 - (float(rank) / float(min_rank))))

        candidate = {
            **row,
            "year_for_check": year,
            "student_rank": rank,
            "rank_reference_year": rank_info.get("reference_year"),
            "simulation": bool(rank_info.get("simulation") or year >= 2026),
            "probability": round(probability_value, 6),
            "probability_reason_code": probability_payload.get("probability_reason_code"),
            "rank_ratio": probability_payload.get("rank_ratio"),
            "utility": round(max(0.0, min(1.0, utility)), 6),
            "rsi": 0.75,
            "source_quality": row.get("source_quality") or "A",
            "subject_check_status": subject.get("status"),
            "subject_reason_code": subject.get("reason_code"),
            "subject_match_type": subject.get("match_type"),
            "subject_requirement_raw": (subject.get("evidence") or {}).get("subject_requirement_raw"),
            "evidence_id": subject.get("evidence_id") or row.get("evidence_id"),
            "subject_evidence_id": subject.get("evidence_id"),
            "subject_source_file": subject.get("source_file"),
            "region_check_status": region.get("status"),
            "region_reason_code": region.get("reason_code"),
            "region_match_type": region.get("match_type"),
            "region_evidence_id": region.get("evidence_id"),
            "region_source_file": region.get("source_files"),
            "province": region.get("province") or row.get("province") or "",
            "city": region.get("city") or row.get("city") or "",
            "preference_fit": round(pref_score, 6),
            "matched_preferences": matched_prefs,
            "location_fit": round(reg_score, 6),
            "value_opportunity": round(value_opportunity, 6),
            "major_value": 0.78 if matched_prefs else 0.45,
            "school_value": 0.65 if "大学" in str(row.get("school_name")) else 0.45,
            "plan_stability": 0.65 if int(row.get("plan_count") or 0) >= 5 else 0.45,
        }

        if subject.get("status") == "BLOCK":
            blocked_rows.append(candidate)
            continue
        if hard_region and region.get("status") != "MATCH":
            blocked_rows.append({**candidate, "blocked_reason": "REGION_HARD_GATE_NOT_MATCH"})
            continue
        if subject.get("status") == "REVIEW" or region.get("status") == "REVIEW":
            review_rows.append(candidate)
            continue
        candidates.append(candidate)
        if len(candidates) >= max_rows:
            break

    return {
        "student": profile,
        "rank_info": rank_info,
        "subjects": subjects,
        "preferences": prefs,
        "simulation": bool(rank_info.get("simulation") or year >= 2026),
        "hard_region": hard_region,
        "candidates": candidates,
        "review_rows": review_rows[:200],
        "blocked_rows": blocked_rows[:200],
        "counts": {
            "candidates": len(candidates),
            "review": len(review_rows),
            "blocked": len(blocked_rows),
        },
    }


def write_candidate_pool(pool: dict[str, Any], out_path: Path) -> Path:
    safe_path = ensure_students_path(out_path)
    write_json(safe_path, pool)
    return safe_path


def main_generate(student_path: Path, out_path: Path, *, hard_region: bool = False) -> dict[str, Any]:
    profile = load_student_profile(student_path)
    pool = build_candidate_pool(profile, hard_region=hard_region)
    write_candidate_pool(pool, out_path)
    pool["output_file"] = rel(out_path)
    return pool
