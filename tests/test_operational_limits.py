import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from api import create_app
from orbitlens.client_ip import client_ip
from orbitlens.config import Settings
from orbitlens.downloads import DownloadBudget, DownloadError, download_to_file
from orbitlens.execution import DeadlineExceeded, execution_budget, request_timeout, wait_retry
from orbitlens.irsa_client import IrsaError, query_collection
from orbitlens.jobs import Job, JobManager, JobQuotaError, JobStore


def test_untrusted_peer_cannot_spoof_forwarded_ip():
    assert client_ip("203.0.113.4", "1.2.3.4", ()) == "203.0.113.4"
    assert client_ip("203.0.113.4", "1.2.3.4", ("127.0.0.1/32",)) == "203.0.113.4"


def test_proxy_chain_is_traversed_from_right_and_bad_headers_ignored():
    trusted = ("10.0.0.0/8",)
    assert client_ip("10.0.0.1", "1.2.3.4, 203.0.113.4, 10.0.0.2", trusted) == "203.0.113.4"
    assert client_ip("10.0.0.1", "garbage, 203.0.113.4", trusted) == "10.0.0.1"
    assert client_ip("::1", "2001:db8::1", ("::1/128",)) == "2001:db8::1"


def test_quota_counts_new_work_not_deduplication_and_releases_active():
    manager = JobManager(max_workers=1, max_active_per_ip=1)
    gate = threading.Event()
    started = threading.Event()
    try:
        first, _ = manager.submit({}, "one", lambda job: (started.set(), gate.wait(2), job.update(status="empty")), owner="ip")
        assert started.wait(2)
        same, created = manager.submit({}, "one", lambda job: None, owner="ip")
        assert same.id == first.id and not created
        with pytest.raises(JobQuotaError, match="activos por IP"):
            manager.submit({}, "two", lambda job: None, owner="ip")
        other, _ = manager.submit({}, "other", lambda job: job.update(status="empty"), owner="other")
        assert other.public()["queue_position"] == 1
    finally:
        gate.set()
        manager.shutdown(wait=True)


def test_sliding_rate_window_and_retry_after():
    now = [100.0]
    manager = JobManager(max_workers=1, searches_per_minute=1, clock=lambda: now[0])
    done = threading.Event()
    try:
        manager.submit({}, "first", lambda job: (job.update(status="empty"), done.set()), owner="ip")
        assert done.wait(2)
        with pytest.raises(JobQuotaError) as error:
            manager.submit({}, "second", lambda job: None, owner="ip")
        assert error.value.retry_after == 60
        now[0] += 61
        manager.submit({}, "third", lambda job: job.update(status="empty"), owner="ip")
    finally:
        manager.shutdown(wait=True)


def test_job_store_recovers_terminal_and_interrupts_running(tmp_path):
    store = JobStore(tmp_path)
    store.save(Job(id="completed", request={}, status="partial", result_id="a" * 16))
    store.save(Job(id="unfinished", request={}, status="running"))
    (tmp_path / "broken.json").write_text("not json")
    manager = JobManager(store_dir=tmp_path)
    try:
        assert manager.active_count == 0
        assert manager.get("completed").result_id == "a" * 16
        assert manager.get("unfinished").status == "error"
        assert "reinicio" in manager.get("unfinished").error
    finally:
        manager.shutdown()


def test_job_updates_are_persisted(tmp_path):
    manager = JobManager(store_dir=tmp_path)
    done = threading.Event()
    job, _ = manager.submit({}, "job", lambda current: (current.update(status="empty"), done.set()))
    assert done.wait(2)
    manager.shutdown(wait=True)
    restored = JobStore(tmp_path).load()[job.id]
    assert restored.status == "empty"


def test_api_quota_returns_retry_after_and_polling_is_free(tmp_path):
    class Service:
        def run(self, job, request):
            gate.wait(2)
            job.update(status="empty")

    gate = threading.Event()
    manager = JobManager(max_active_per_ip=1)
    try:
        with TestClient(create_app(settings=Settings(data_dir=tmp_path), service=Service(), manager=manager)) as client:
            first = client.post("/api/search", json={"target_name": "barnard"})
            assert first.status_code == 202
            blocked = client.post("/api/search", json={"target_name": "rw_aur"},
                                  headers={"X-Forwarded-For": "fake"})
            assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0
            assert client.get(first.json()["status_url"]).status_code == 200
            assert client.get("/api/health").status_code == 200
            gate.set()
    finally:
        gate.set()
        manager.shutdown(wait=True)


def test_retry_after_cannot_exceed_job_budget(tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(503, headers={"Retry-After": "600"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with execution_budget(1), pytest.raises(DeadlineExceeded):
            download_to_file(client, "https://example.test/file", tmp_path / "file.fits",
                             max_bytes=1000, attempts=3)
    assert len(calls) == 1
    assert not list(tmp_path.glob("*.part"))


def test_download_permanent_error_is_not_retried(tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(DownloadError):
            download_to_file(client, "https://example.test/file", tmp_path / "file.fits", max_bytes=100, attempts=3)
    assert len(calls) == 1


def test_failed_oversize_response_consumes_bytes(tmp_path):
    budget = DownloadBudget(10000)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 200))) as client:
        with pytest.raises(DownloadError):
            download_to_file(client, "https://example.test/file", tmp_path / "file.fits", max_bytes=100, budget=budget)
    assert budget.used == 200
    assert not list(tmp_path.iterdir())


def test_sia_limits_body_size_and_retry_after():
    from dataclasses import replace

    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 20))) as client:
        with pytest.raises(IrsaError, match="excede"):
            query_collection(client, replace(Settings(), max_sia_bytes=10), "spherex_dr1", 10, 20, 1)
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429, headers={"Retry-After": "10"}))) as client:
        with execution_budget(1), pytest.raises(DeadlineExceeded):
            query_collection(client, Settings(), "spherex_dr1", 10, 20, 1)


def test_timeout_is_capped_and_context_is_restored():
    with httpx.Client(timeout=120) as client:
        with execution_budget(1):
            assert request_timeout(client).read <= 1
            with pytest.raises(DeadlineExceeded):
                wait_retry(2)
        assert request_timeout(client).read == 120
