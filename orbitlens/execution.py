"""Presupuesto temporal cooperativo compartido por red, esperas y procesamiento."""

from __future__ import annotations

import math
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx


class DeadlineExceeded(TimeoutError):
    pass


@dataclass
class Deadline:
    end: float

    def remaining(self) -> float:
        value = self.end - time.monotonic()
        if value <= 0:
            raise DeadlineExceeded("presupuesto temporal del trabajo agotado")
        return value


_current: ContextVar[Deadline | None] = ContextVar("orbitlens_deadline", default=None)


@contextmanager
def execution_budget(seconds: float):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("presupuesto temporal debe ser finito y positivo")
    previous = _current.get()
    end = time.monotonic() + seconds
    token = _current.set(Deadline(min(end, previous.end) if previous else end))
    try:
        check_deadline()
        yield
        check_deadline()
    finally:
        _current.reset(token)


def check_deadline() -> None:
    if deadline := _current.get():
        deadline.remaining()


def remaining_seconds() -> float | None:
    deadline = _current.get()
    return deadline.remaining() if deadline else None


def request_timeout(client: httpx.Client) -> httpx.Timeout:
    remaining = remaining_seconds()
    values = client.timeout.as_dict()
    if remaining is not None:
        values = {key: min(value, remaining) if value is not None else remaining
                  for key, value in values.items()}
    return httpx.Timeout(**values)


def retry_delay(value: str | None, fallback: float) -> float:
    if value:
        try:
            seconds = float(value)
        except ValueError:
            try:
                seconds = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                seconds = fallback
        if math.isfinite(seconds):
            return max(0.0, seconds)
    return fallback


def wait_retry(seconds: float) -> None:
    remaining = remaining_seconds()
    if remaining is not None and seconds >= remaining:
        raise DeadlineExceeded("Retry-After/backoff excede el presupuesto temporal restante")
    time.sleep(seconds)
    check_deadline()
