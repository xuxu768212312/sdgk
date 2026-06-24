from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_project_files_exist() -> None:
    frontend = ROOT / "frontend"
    assert (frontend / "package.json").exists()
    assert (frontend / "src" / "App.vue").exists()
    assert (frontend / "src" / "api" / "client.ts").exists()
    assert (frontend / "src" / "views" / "PlanReview.vue").exists()
