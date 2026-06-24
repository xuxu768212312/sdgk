from __future__ import annotations

import hashlib
import itertools
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from sdgk.core.paths import ROOT, ensure_students_path


_counter = itertools.count(1)
JOBS: dict[str, dict[str, Any]] = {}
FILES: dict[str, Path] = {}


def new_job(kind: str) -> str:
    job_id = f"job_{next(_counter):06d}"
    JOBS[job_id] = {
        "job_id": job_id,
        "kind": kind,
        "status": "queued",
        "progress": 0,
        "logs": [],
        "outputs": {},
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    return job_id


def log(job_id: str, message: str) -> None:
    JOBS[job_id]["logs"].append(message)


def register_file(path: Path) -> str:
    resolved = ensure_students_path(path)
    file_id = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:24]
    FILES[file_id] = resolved
    return file_id


def get_file(file_id: str) -> Path:
    if file_id not in FILES:
        raise KeyError(file_id)
    path = FILES[file_id]
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def run_sync(job_id: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    job = JOBS[job_id]
    job["status"] = "running"
    job["progress"] = 10
    try:
        result = fn()
        outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
        file_ids: dict[str, str] = {}
        for key, value in outputs.items():
            try:
                file_ids[key] = register_file(Path(value) if Path(value).is_absolute() else ROOT / value)
            except Exception:
                continue
        job.update(
            {
                "status": "succeeded",
                "progress": 100,
                "result": result,
                "outputs": outputs,
                "file_ids": file_ids,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    except Exception as exc:
        job.update(
            {
                "status": "failed",
                "progress": 100,
                "reason_code": exc.__class__.__name__,
                "error": str(exc),
                "finished_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return job
