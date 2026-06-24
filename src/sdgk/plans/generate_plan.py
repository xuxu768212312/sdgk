from __future__ import annotations

from pathlib import Path
from typing import Any

from sdgk.audits.final_plan_audit import audit_plan_rows
from sdgk.core.io import write_json
from sdgk.core.paths import ensure_students_path, rel
from sdgk.plans.candidate_pool import build_candidate_pool, load_student_profile
from sdgk.plans.excel_writer import write_plan_workbook
from sdgk.plans.markdown_report import write_markdown_report
from sdgk.strategy.optimizer import optimize_candidates


def generate_plan(
    *,
    student_path: Path,
    out_dir: Path,
    risk_profile: str = "standard",
    hard_region: bool = False,
    slots: int = 96,
) -> dict[str, Any]:
    profile = load_student_profile(student_path)
    safe_out = ensure_students_path(out_dir)
    safe_out.mkdir(parents=True, exist_ok=True)

    pool = build_candidate_pool(profile, hard_region=hard_region)
    strategy = optimize_candidates(pool["candidates"], slots=slots, risk_profile=risk_profile)
    final_audit = audit_plan_rows(strategy.get("selected", []), strategy_result=strategy)
    final_audit["simulation"] = bool(pool.get("simulation"))
    if pool.get("simulation"):
        final_audit.setdefault("warnings", []).append("SIMULATION_MODE_2026_PLAN_PENDING")

    outputs = {
        "candidate_pool": safe_out / "candidate_pool.json",
        "strategy_result": safe_out / "strategy_result.json",
        "final_audit": safe_out / "final_audit.json",
        "plan_meta": safe_out / "plan_meta.json",
        "excel": safe_out / "志愿表.xlsx",
        "markdown": safe_out / "详细报告.md",
    }
    write_json(outputs["candidate_pool"], pool)
    write_json(outputs["strategy_result"], strategy)
    write_json(outputs["final_audit"], final_audit)

    # Reserved report slots keep the v3.9 directory contract stable even when
    # a specific audit has no independent row-level payload in simulation mode.
    write_json(safe_out / "subject_audit.json", {"source": "candidate_pool", "hard_gate": "see final_audit"})
    write_json(safe_out / "region_audit.json", {"source": "candidate_pool", "hard_gate": "see final_audit"})
    (safe_out / "report_assets").mkdir(exist_ok=True)

    write_plan_workbook(
        out_path=outputs["excel"],
        profile=profile,
        candidate_pool=pool,
        strategy_result=strategy,
        final_audit=final_audit,
    )
    write_markdown_report(
        out_path=outputs["markdown"],
        profile=profile,
        candidate_pool=pool,
        strategy_result=strategy,
        final_audit=final_audit,
    )
    meta = {
        "student_file": rel(student_path),
        "out_dir": rel(safe_out),
        "risk_profile": risk_profile,
        "slots": slots,
        "hard_region": hard_region,
        "hard_gate_passed": final_audit.get("hard_gate_passed"),
        "simulation": final_audit.get("simulation"),
        "outputs": {key: rel(path) for key, path in outputs.items()},
    }
    write_json(outputs["plan_meta"], meta)
    return {
        **meta,
        "candidate_counts": pool.get("counts"),
        "violations": final_audit.get("violations", []),
        "strategy_result": strategy,
        "final_audit": final_audit,
    }
