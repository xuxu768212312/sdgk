from __future__ import annotations

from sdgk.plans.candidate_pool import build_candidate_pool


def test_candidate_pool_uses_subject_and_region_gates() -> None:
    profile = {
        "name": "测试考生",
        "year": 2026,
        "level": "本科",
        "score": 495,
        "subjects": ["历史", "生物", "思想政治"],
        "regions": ["山东", "苏州"],
        "major_preferences": ["师范", "法学", "英语", "金融", "生物工程"],
    }
    pool = build_candidate_pool(profile, limit=800, max_rows=120)
    assert pool["counts"]["candidates"] > 0
    assert all(row["subject_check_status"] == "PASS" for row in pool["candidates"])
    assert all(row.get("program_id") and row.get("evidence_id") and row.get("source_file") for row in pool["candidates"])
    assert any(row["region_check_status"] == "MATCH" for row in pool["candidates"])
