from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from api import create_app
from orbitlens.api_models import SearchRequest
from orbitlens.config import Settings
from orbitlens.jobs import TERMINAL_STATES, JobManager


class StubService:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def run(self, job, request) -> None:
        self.requests.append(dict(request))
        job.update(status="ready", phase=None, result_id="a" * 16)
        job.set_counts(processed=3, downloaded=3)

    def close(self) -> None:
        pass


@pytest.fixture()
def client_and_settings(tmp_path):
    settings = Settings(data_dir=tmp_path)
    service = StubService()
    manager = JobManager(max_workers=1)
    app = create_app(settings=settings, service=service, manager=manager)
    with TestClient(app) as client:
        yield client, settings, service, manager
    manager.shutdown()


def _wait(client, job_id: str, timeout: float = 2.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/status/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in TERMINAL_STATES:
            return payload
        time.sleep(0.01)
    raise AssertionError("el trabajo no terminó a tiempo")


def test_health(client_and_settings) -> None:
    client, settings, _, _ = client_and_settings
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["pipeline_version"]
    assert "spherex_dr1" in payload["collections"]


def test_presets(client_and_settings) -> None:
    client, _, _, _ = client_and_settings
    response = client.get("/api/presets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 5
    assert {item["id"] for item in payload["presets"]} == {
        "barnard",
        "epsindi_b",
        "wise0855",
        "rw_aur",
        "r_dra",
    }


def test_search_by_target_name(client_and_settings) -> None:
    client, _, service, _ = client_and_settings
    response = client.post("/api/search", json={"target_name": "barnard"})
    assert response.status_code == 202
    payload = response.json()
    assert payload["job_id"]
    assert payload["deduplicated"] is False

    finished = _wait(client, payload["job_id"])
    assert finished["status"] == "ready"
    assert finished["result_id"] == "a" * 16
    assert service.requests[0]["ra_deg"] == pytest.approx(269.45208)


def test_search_accepts_sexagesimal(client_and_settings) -> None:
    client, _, service, _ = client_and_settings
    response = client.post(
        "/api/search",
        json={
            "ra_deg": "17 57 48.5",
            "dec_deg": "+04 41 36",
            "sexagesimal": True,
            "frames": 6,
        },
    )
    assert response.status_code == 202
    _wait(client, response.json()["job_id"])
    assert service.requests[-1]["ra_deg"] == pytest.approx(269.45208333)
    assert service.requests[-1]["frames"] == 6


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"target_name": "Planeta X"},
        {"target_name": "barnard", "ra_deg": 10, "dec_deg": 20},
        {"ra_deg": 400, "dec_deg": 20},
        {"ra_deg": 10, "dec_deg": 95},
        {"ra_deg": 10, "dec_deg": 20, "frames": 99},
        {"ra_deg": 10, "dec_deg": 20, "fov_arcmin": 0},
        {"ra_deg": 10, "dec_deg": 20, "detector": "D9"},
    ],
)
def test_invalid_search_payloads(client_and_settings, payload) -> None:
    client, _, _, _ = client_and_settings
    response = client.post("/api/search", json=payload)
    assert response.status_code == 422


def test_unknown_job(client_and_settings) -> None:
    client, _, _, _ = client_and_settings
    assert client.get("/api/status/nope").status_code == 404


def test_unknown_manifest(client_and_settings) -> None:
    client, _, _, _ = client_and_settings
    assert client.get("/api/results/not-a-result/manifest").status_code == 404
    assert client.get(f"/api/results/{'b' * 16}/manifest").status_code == 404


def test_manifest_and_indexed_file(client_and_settings) -> None:
    client, settings, _, _ = client_and_settings
    result_id = "b" * 16
    result_dir = settings.data_dir / "results" / result_id
    frames = result_dir / "frames"
    frames.mkdir(parents=True)
    image = frames / "frame.png"
    image.write_bytes(b"png")

    manifest = {
        "schema_version": 1,
        "pipeline_version": "0.1.0",
        "code_commit": "test",
        "result_id": result_id,
        "created_at": "2026-11-14T00:00:00Z",
        "request": {},
        "search": {},
        "grid": {},
        "processing": {},
        "frames": [
            {
                "frame_id": "01_x",
                "png": "frames/frame.png",
                "fits": "frames/frame.fits",
                "time": {},
            }
        ],
        "files": [
            {
                "id": "01_x-png",
                "kind": "png",
                "path": "frames/frame.png",
                "sha256": "x",
                "bytes": 3,
            }
        ],
        "warnings": [],
    }
    (result_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    assert client.get(f"/api/results/{result_id}/manifest").status_code == 200
    file_response = client.get(f"/api/results/{result_id}/files/01_x-png")
    assert file_response.status_code == 200
    assert file_response.content == b"png"
    assert client.get(f"/api/results/{result_id}/files/unknown").status_code == 404


def test_file_path_traversal_blocked(client_and_settings) -> None:
    client, settings, _, _ = client_and_settings
    result_id = "c" * 16
    result_dir = settings.data_dir / "results" / result_id
    result_dir.mkdir(parents=True)
    (settings.data_dir / "secret.txt").write_text("no", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "pipeline_version": "0.1.0",
        "code_commit": "test",
        "result_id": result_id,
        "created_at": "2026-11-14T00:00:00Z",
        "request": {},
        "search": {},
        "grid": {},
        "processing": {},
        "frames": [
            {
                "frame_id": "01_x",
                "png": "frames/frame.png",
                "fits": "frames/frame.fits",
                "time": {},
            }
        ],
        "files": [
            {"id": "escape", "kind": "png", "path": "../secret.txt", "sha256": "x", "bytes": 2}
        ],
        "warnings": [],
    }
    (result_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert client.get(f"/api/results/{result_id}/files/escape").status_code == 404


def test_request_model_normalizes_units() -> None:
    request = SearchRequest(
        ra_deg="17 57 48.5",
        dec_deg="+04 41 36",
        sexagesimal=True,
        detector="d1",
    )
    normalized = request.normalized()
    assert normalized["ra_deg"] == pytest.approx(269.45208333, abs=1e-6)
    assert normalized["detector"] == "D1"
