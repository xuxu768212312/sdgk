from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from sdgk.api.jobs import JOBS, get_file, new_job, run_sync
from sdgk.api.schemas import CandidateGenerateRequest, CodeAliasRequest, PlanGenerateRequest, ProgramSearchRequest, RegionCheckRequest, SearchRequest, SubjectCheckRequest
from sdgk.core.io import write_json
from sdgk.core.paths import ROOT, STUDENTS_DIR, ensure_students_path, rel
from sdgk.indexes.master import major_code_aliases, school_code_aliases, search_majors, search_programs, search_schools, summary as master_summary
from sdgk.indexes.region import check_school_regions, split_regions
from sdgk.indexes.subject import check_eligibility
from sdgk.plans.candidate_pool import build_candidate_pool
from sdgk.plans.generate_plan import generate_plan


app = FastAPI(title="山东高考知识库本地 API", version="3.10.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_regions(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return split_regions(value)
    regions: list[str] = []
    for item in value:
        regions.extend(split_regions(item))
    return regions


def profile_student_path(profile: dict[str, Any]) -> Path:
    name = str(profile.get("name") or profile.get("姓名") or "未命名考生").strip()
    safe_name = "".join(ch for ch in name if ch not in r"\/:*?<>|") or "未命名考生"
    path = STUDENTS_DIR / safe_name / "基本信息.json"
    write_json(path, profile)
    return path


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "3.10.1",
        "workspace": str(ROOT),
        "time": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/audit/status")
def audit_status() -> dict[str, Any]:
    reports = sorted((ROOT / "wiki").glob("data_accuracy_report_*.json"))
    latest = reports[-1] if reports else None
    return {
        "latest_report": rel(latest) if latest else None,
        "status": "UNKNOWN" if latest is None else "AVAILABLE",
        "message": "请运行 python -m sdgk audit data --full-subject-reextract 获取最新审计。" if latest is None else "存在历史审计报告。",
    }


@app.get("/api/indexes/summary")
def indexes_summary() -> dict[str, Any]:
    subject_db = ROOT / "processed" / "选科要求" / "subject_index.sqlite"
    region_db = ROOT / "processed" / "院校地区" / "school_region_index.sqlite"
    return {
        "subject_index": {"exists": subject_db.exists(), "file": rel(subject_db)},
        "region_index": {"exists": region_db.exists(), "file": rel(region_db)},
        "master_index": master_summary(),
    }


@app.post("/api/check/subject")
def api_check_subject(payload: SubjectCheckRequest) -> dict[str, Any]:
    return check_eligibility(**payload.model_dump())


@app.post("/api/check/region")
def api_check_region(payload: RegionCheckRequest) -> dict[str, Any]:
    return check_school_regions(
        normalize_regions(payload.regions),
        school_name=payload.school_name or "",
        subject_school_code=payload.school_code or "",
    )


@app.post("/api/master/search-schools")
def api_search_schools(payload: SearchRequest) -> list[dict[str, Any]]:
    return search_schools(payload.query, limit=payload.limit)


@app.post("/api/master/search-majors")
def api_search_majors(payload: SearchRequest) -> list[dict[str, Any]]:
    return search_majors(payload.query, limit=payload.limit)


@app.post("/api/master/search-programs")
def api_search_programs(payload: ProgramSearchRequest) -> list[dict[str, Any]]:
    return search_programs(**payload.model_dump())


@app.post("/api/master/school-code-aliases")
def api_school_code_aliases(payload: CodeAliasRequest) -> list[dict[str, Any]]:
    return school_code_aliases(school_id=payload.school_id, school_code=payload.code, limit=payload.limit)


@app.post("/api/master/major-code-aliases")
def api_major_code_aliases(payload: CodeAliasRequest) -> list[dict[str, Any]]:
    return major_code_aliases(major_id=payload.major_id, major_code=payload.code, limit=payload.limit)


@app.post("/api/candidates/generate")
def api_candidates_generate(payload: CandidateGenerateRequest) -> dict[str, Any]:
    return build_candidate_pool(payload.profile, hard_region=payload.hard_region)


@app.post("/api/plans/generate")
def api_plan_generate(payload: PlanGenerateRequest) -> dict[str, Any]:
    job_id = new_job("plan.generate")

    def work() -> dict[str, Any]:
        if payload.student_file:
            student_path = ensure_students_path(payload.student_file)
        elif payload.profile:
            student_path = profile_student_path(payload.profile)
        else:
            raise ValueError("profile or student_file is required")
        if payload.out_dir:
            out_dir = ensure_students_path(payload.out_dir)
        else:
            profile = payload.profile or {}
            name = str(profile.get("name") or profile.get("姓名") or student_path.parent.name)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = STUDENTS_DIR / name / "志愿方案" / f"api_{stamp}"
        return generate_plan(
            student_path=student_path,
            out_dir=out_dir,
            risk_profile=payload.risk_profile,
            hard_region=payload.hard_region,
            slots=payload.slots,
        )

    return run_sync(job_id, work)


@app.get("/api/jobs/{job_id}")
def api_get_job(job_id: str) -> dict[str, Any]:
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="job not found")
    return JOBS[job_id]


@app.get("/api/files/{file_id}")
def api_get_file(file_id: str) -> FileResponse:
    try:
        path = get_file(file_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="file not found") from exc
    return FileResponse(path)
