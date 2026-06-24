from __future__ import annotations

from fastapi.testclient import TestClient

from sdgk.api.app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_subject_api_blocks_wrong_subjects() -> None:
    response = client.post(
        "/api/check/subject",
        json={
            "year": 2026,
            "level": "本科",
            "subjects": ["历史", "生物", "思想政治"],
            "school_code": "10001",
            "major_code": "0060",
            "school_name": "北京大学",
            "major_name": "工科试验班类",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] in {"BLOCK", "REVIEW"}


def test_region_api_qingdao_university() -> None:
    response = client.post("/api/check/region", json={"regions": ["山东"], "school_name": "青岛大学"})
    assert response.status_code == 200
    assert response.json()["status"] == "MATCH"


def test_plan_api_rejects_path_traversal() -> None:
    response = client.post(
        "/api/plans/generate",
        json={
            "profile": {
                "name": "路径测试",
                "year": 2026,
                "level": "本科",
                "score": 495,
                "subjects": ["历史", "生物", "思想政治"],
            },
            "out_dir": "../outside",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["reason_code"] == "ValueError"
