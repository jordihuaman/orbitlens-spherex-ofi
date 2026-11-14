from __future__ import annotations

import threading
import time

import pytest

from orbitlens.jobs import TERMINAL_STATES, JobCapacityError, JobManager


def _wait_until_terminal(manager: JobManager, job_id: str, timeout: float = 2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = manager.get(job_id)
        if job is not None and job.status in TERMINAL_STATES:
            return job
        time.sleep(0.01)
    raise AssertionError("el trabajo no terminó a tiempo")


def test_deduplicates_inflight_jobs() -> None:
    manager = JobManager(max_workers=1)
    gate = threading.Event()

    def work(job) -> None:
        gate.wait(2.0)
        job.update(status="ready")

    try:
        first, created_first = manager.submit({}, "same", work)
        second, created_second = manager.submit({}, "same", work)
        assert created_first
        assert not created_second
        assert first.id == second.id
    finally:
        gate.set()
        _wait_until_terminal(manager, first.id)
        manager.shutdown()


def test_capacity_limit() -> None:
    manager = JobManager(max_workers=1, max_active=1)
    gate = threading.Event()

    def work(job) -> None:
        gate.wait(2.0)
        job.update(status="ready")

    try:
        manager.submit({}, "one", work)
        with pytest.raises(JobCapacityError):
            manager.submit({}, "two", work)
    finally:
        gate.set()
        manager.shutdown()


def test_exception_becomes_error_status() -> None:
    manager = JobManager(max_workers=1)

    def work(job) -> None:
        raise ValueError("fallo controlado")

    try:
        job, _ = manager.submit({}, "error", work)
        finished = _wait_until_terminal(manager, job.id)
        assert finished.status == "error"
        assert "fallo controlado" in (finished.error or "")
    finally:
        manager.shutdown()


def test_public_payload_has_status_url() -> None:
    manager = JobManager(max_workers=1)

    def work(job) -> None:
        job.update(status="empty")

    try:
        job, _ = manager.submit({"ra_deg": 1}, "payload", work)
        finished = _wait_until_terminal(manager, job.id)
        payload = finished.public()
        assert payload["status"] == "empty"
        assert payload["status_url"] == f"/api/status/{job.id}"
        assert payload["request"] == {"ra_deg": 1}
    finally:
        manager.shutdown()
