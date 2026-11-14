"""Cola de trabajos en memoria, con estados explícitos y deduplicación."""

from __future__ import annotations

import hashlib
import math
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .manifest import read_json, write_json_atomic

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
    queue_position: int | None = None
    _on_change: Callable | None = field(default=None, repr=False, compare=False)
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
        self._notify()

    def add_warning(self, message: str) -> None:
        with self._lock:
            if message not in self.warnings:
                self.warnings.append(message)
            self.updated_at = _now()
        self._notify()

    def set_counts(self, **counts: int) -> None:
        with self._lock:
            self.counts.update({key: int(value) for key, value in counts.items()})
            self.updated_at = _now()
        self._notify()

    def _notify(self) -> None:
        if self._on_change is not None:
            self._on_change(self)

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
                "queue_position": self.queue_position,
            }


class JobCapacityError(RuntimeError):
    """La cola alcanzó el máximo de trabajos activos."""


class JobQuotaError(JobCapacityError):
    def __init__(self, message: str, retry_after: int = 30):
        super().__init__(message)
        self.retry_after = retry_after


class JobStore:
    """Snapshots atómicos; un proceso propietario por directorio."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save(self, job: Job) -> None:
        with self._lock:
            write_json_atomic(job.public(), self.root / f"{job.id}.json")

    def load(self) -> dict[str, Job]:
        jobs = {}
        for path in self.root.glob("*.json"):
            try:
                item = read_json(path)
                if item["job_id"] != path.stem or not isinstance(item["request"], dict):
                    continue
                job = Job(id=item["job_id"], request=item["request"])
                for key in ("status", "phase", "created_at", "updated_at", "result_id", "error", "warnings", "counts"):
                    if key in item:
                        setattr(job, key, item[key])
                if job.status not in TERMINAL_STATES:
                    job.update(status="error", phase=None,
                               error="trabajo interrumpido por reinicio; puede volver a intentarlo")
                self.save(job)
                job._on_change = self.save
                jobs[job.id] = job
            except (OSError, ValueError, TypeError, KeyError):
                # Un snapshot corrupto no impide recuperar el resto.
                continue
        return jobs


class JobManager:
    def __init__(self, *, max_workers: int = 3, max_active: int = 32,
                 max_active_per_ip: int = 2, searches_per_minute: int = 10,
                 store_dir: Path | None = None, clock: Callable = time.monotonic) -> None:
        if max_workers < 1 or max_active < 1:
            raise ValueError("max_workers y max_active deben ser >= 1")
        self._store = JobStore(store_dir) if store_dir else None
        self._jobs: dict[str, Job] = self._store.load() if self._store else {}
        self._inflight: dict[str, str] = {}
        self._active = 0
        self._max_active = max_active
        self._lock = threading.Lock()
        self._queued: list[str] = []
        self._owners: dict[str, str] = {}
        self._history: dict[str, deque] = {}
        self._max_active_per_ip = max_active_per_ip
        self._searches_per_minute = searches_per_minute
        self._clock = clock
        self._closing = False
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="orbitlens"
        )

    @property
    def active_count(self) -> int:
        with self._lock:
            return self._active

    def submit(
        self, request: dict[str, object], key: str, work: Callable[[Job], None],
        *, owner: str | None = None,
    ) -> tuple[Job, bool]:
        """Encola un trabajo. Devuelve ``(job, creado)``.

        Si ya hay un trabajo equivalente en curso, se reutiliza en lugar de
        duplicar descargas y cómputo.
        """

        with self._lock:
            if self._closing:
                raise JobCapacityError("servicio cerrándose; reintente")
            existing_id = self._inflight.get(key)
            if existing_id is not None:
                existing = self._jobs.get(existing_id)
                if existing is not None and existing.status not in TERMINAL_STATES:
                    return existing, False
                self._inflight.pop(key, None)

            # Solo trabajo nuevo consume cuota. No se persisten direcciones IP.
            owner_key = hashlib.sha256(owner.encode()).hexdigest() if owner is not None else None
            if owner_key is not None:
                now = self._clock()
                for ip, timestamps in list(self._history.items()):
                    while timestamps and timestamps[0] <= now - 60:
                        timestamps.popleft()
                    if not timestamps:
                        del self._history[ip]
                history = self._history.get(owner_key, deque())
                if len(history) >= self._searches_per_minute:
                    raise JobQuotaError("cuota de búsquedas por minuto agotada",
                                        max(1, math.ceil(60 - (now - history[0]))))
                if sum(value == owner_key for value in self._owners.values()) >= self._max_active_per_ip:
                    raise JobQuotaError("máximo de trabajos activos por IP alcanzado")

            if self._active >= self._max_active:
                raise JobCapacityError(
                    f"cola llena: {self._active} trabajos activos (máximo {self._max_active})"
                )

            job = Job(id=uuid.uuid4().hex[:12], request=dict(request))
            if self._store:
                job._on_change = self._store.save
            self._jobs[job.id] = job
            self._inflight[key] = job.id
            self._active += 1
            self._queued.append(job.id)
            if owner_key is not None:
                self._owners[job.id] = owner_key
                self._history.setdefault(owner_key, deque()).append(self._clock())
            self._refresh_queue()

        self._executor.submit(self._run, job, work)
        return job, True

    def _run(self, job: Job, work: Callable[[Job], None]) -> None:
        try:
            with self._lock:
                if job.id in self._queued:
                    self._queued.remove(job.id)
                job.update(status="running", phase="starting", queue_position=None)
                self._refresh_queue()
            work(job)
            if job.status not in TERMINAL_STATES:
                raise RuntimeError("el trabajo terminó sin estado terminal")
        except Exception as exc:  # noqa: BLE001 - se publica como estado del trabajo
            job.update(
                status="error",
                phase=None,
                error=f"{type(exc).__name__}: {exc}",
            )
        finally:
            with self._lock:
                self._active = max(0, self._active - 1)
                self._owners.pop(job.id, None)
                for key, value in list(self._inflight.items()):
                    if value == job.id:
                        del self._inflight[key]
            job.update(updated_at=_now())

    def _refresh_queue(self) -> None:
        for position, job_id in enumerate(self._queued, start=1):
            self._jobs[job_id].update(queue_position=position)

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def shutdown(self, *, wait: bool = False) -> None:
        with self._lock:
            self._closing = True
            for job_id in self._queued:
                self._jobs[job_id].update(status="error", phase=None, queue_position=None,
                                          error="trabajo cancelado al detener el servicio; reintente")
            self._queued.clear()
        self._executor.shutdown(wait=wait, cancel_futures=True)
