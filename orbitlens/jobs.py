"""Cola de trabajos en memoria, con estados explícitos y deduplicación."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime

__all__ = ["Job", "JobManager", "JobCapacityError", "TERMINAL_STATES"]

TERMINAL_STATES = frozenset({"ready", "partial", "empty", "error"})


def _now() -> str:
    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass
class Job:
    id: str
    request: dict[str, object]
    status: str = "queued"
    phase: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    result_id: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )

    def update(self, **fields: object) -> None:
        with self._lock:
            for key, value in fields.items():
                if not hasattr(self, key):
                    raise AttributeError(f"campo de trabajo desconocido: {key}")
                setattr(self, key, value)
            self.updated_at = _now()

    def add_warning(self, message: str) -> None:
        with self._lock:
            if message not in self.warnings:
                self.warnings.append(message)
            self.updated_at = _now()

    def set_counts(self, **counts: int) -> None:
        with self._lock:
            self.counts.update({key: int(value) for key, value in counts.items()})
            self.updated_at = _now()

    def public(self) -> dict[str, object]:
        with self._lock:
            return {
                "job_id": self.id,
                "status": self.status,
                "phase": self.phase,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "result_id": self.result_id,
                "error": self.error,
                "warnings": list(self.warnings),
                "counts": dict(self.counts),
                "request": dict(self.request),
                "status_url": f"/api/status/{self.id}",
            }


class JobCapacityError(RuntimeError):
    """La cola alcanzó el máximo de trabajos activos."""


class JobManager:
    def __init__(self, *, max_workers: int = 3, max_active: int = 32) -> None:
        if max_workers < 1 or max_active < 1:
            raise ValueError("max_workers y max_active deben ser >= 1")
        self._jobs: dict[str, Job] = {}
        self._inflight: dict[str, str] = {}
        self._active = 0
        self._max_active = max_active
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="orbitlens"
        )

    @property
    def active_count(self) -> int:
        with self._lock:
            return self._active

    def submit(
        self, request: dict[str, object], key: str, work: Callable[[Job], None]
    ) -> tuple[Job, bool]:
        """Encola un trabajo. Devuelve ``(job, creado)``.

        Si ya hay un trabajo equivalente en curso, se reutiliza en lugar de
        duplicar descargas y cómputo.
        """

        with self._lock:
            existing_id = self._inflight.get(key)
            if existing_id is not None:
                existing = self._jobs.get(existing_id)
                if existing is not None and existing.status not in TERMINAL_STATES:
                    return existing, False
                self._inflight.pop(key, None)

            if self._active >= self._max_active:
                raise JobCapacityError(
                    f"cola llena: {self._active} trabajos activos (máximo {self._max_active})"
                )

            job = Job(id=uuid.uuid4().hex[:12], request=dict(request))
            self._jobs[job.id] = job
            self._inflight[key] = job.id
            self._active += 1

        self._executor.submit(self._run, job, work)
        return job, True

    def _run(self, job: Job, work: Callable[[Job], None]) -> None:
        try:
            job.update(status="running", phase="starting")
            work(job)
        except Exception as exc:  # noqa: BLE001 - se publica como estado del trabajo
            job.update(
                status="error",
                phase=None,
                error=f"{type(exc).__name__}: {exc}",
            )
        finally:
            with self._lock:
                self._active = max(0, self._active - 1)
                for key, value in list(self._inflight.items()):
                    if value == job.id:
                        del self._inflight[key]
            job.update(updated_at=_now())

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def shutdown(self, *, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)
