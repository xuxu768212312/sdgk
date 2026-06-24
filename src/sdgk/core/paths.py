from __future__ import annotations

import os
from pathlib import Path


def discover_root() -> Path:
    configured = os.environ.get("SDGK_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "AGENTS.md").exists() and (parent / "processed").exists():
            return parent
    return current.parents[3]


ROOT = discover_root()
RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"
STUDENTS_DIR = ROOT / "students"
WIKI_DIR = ROOT / "wiki"


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def ensure_within_root(path: Path | str, *, base: Path = ROOT) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = base / resolved
    resolved = resolved.resolve()
    base_resolved = base.resolve()
    if base_resolved != resolved and base_resolved not in resolved.parents:
        raise ValueError(f"path escapes workspace root: {resolved}")
    return resolved


def ensure_students_path(path: Path | str) -> Path:
    raw = Path(path).expanduser()
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        root_candidate = (ROOT / raw).resolve()
        if root_candidate == STUDENTS_DIR.resolve() or STUDENTS_DIR.resolve() in root_candidate.parents:
            resolved = root_candidate
        else:
            resolved = (STUDENTS_DIR / raw).resolve()
    students_resolved = STUDENTS_DIR.resolve()
    if students_resolved != resolved and students_resolved not in resolved.parents:
        raise ValueError(f"path escapes students workspace: {resolved}")
    return resolved
