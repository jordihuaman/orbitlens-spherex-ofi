"""Descarga acotada de recortes FITS, con presupuesto y validación básica."""

from __future__ import annotations

import os
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx

from .execution import (
    DeadlineExceeded,
    check_deadline,
    remaining_seconds,
    request_timeout,
    retry_delay,
    wait_retry,
)
from .network_policy import validate_remote_url

_SLOTS = threading.BoundedSemaphore(3)

__all__ = ["DownloadError", "DownloadBudget", "download_to_file", "is_probably_fits"]


class DownloadError(RuntimeError):
    """Fallo de descarga, tamaño excesivo o contenido no FITS."""

    def __init__(self, message: str, *, transient: bool = False, retry_after: str | None = None):
        super().__init__(message)
        self.transient = transient
        self.retry_after = retry_after


@dataclass
class DownloadBudget:
    """Presupuesto compartido por todas las descargas de un trabajo."""

    max_bytes: int
    used: int = 0

    def consume(self, amount: int) -> None:
        self.used += amount
        if self.used > self.max_bytes:
            raise DownloadError(
                f"presupuesto de descarga agotado: {self.used} > {self.max_bytes} bytes"
            )


def is_probably_fits(path: Path) -> bool:
    try:
        with Path(path).open("rb") as handle:
            head = handle.read(80)
    except OSError:
        return False
    return head.startswith(b"SIMPLE  =") or head.startswith(b"\x1f\x8b")


def _download_once(
    client: httpx.Client,
    url: str,
    destination: Path,
    *,
    max_bytes: int,
    budget: DownloadBudget | None,
    chunk_size: int,
    space_check: Callable[[int], None] | None = None,
) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + f".{uuid.uuid4().hex}.part")

    total = 0
    try:
        check_deadline()
        with client.stream("GET", url, follow_redirects=False, timeout=request_timeout(client)) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_bytes(chunk_size):
                    check_deadline()
                    if not chunk:
                        continue
                    total += len(chunk)
                    if budget is not None:
                        budget.consume(len(chunk))
                    if space_check is not None:
                        space_check(len(chunk))
                    if total > max_bytes:
                        raise DownloadError(
                            f"respuesta mayor que {max_bytes} bytes: {url}"
                        )
                    handle.write(chunk)
            check_deadline()
            metadata = {key: response.headers.get(key) for key in ("etag", "last-modified")
                        if response.headers.get(key)}
    except httpx.HTTPError as exc:
        temporary.unlink(missing_ok=True)
        response = exc.response if isinstance(exc, httpx.HTTPStatusError) else None
        transient = response is None or response.status_code in {429, 500, 502, 503, 504}
        raise DownloadError(f"descarga fallida {url}: {exc}", transient=transient,
                            retry_after=response.headers.get("Retry-After") if response is not None else None) from exc
    except (DeadlineExceeded, RuntimeError):
        temporary.unlink(missing_ok=True)
        raise
    except DownloadError:
        temporary.unlink(missing_ok=True)
        raise
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise DownloadError(f"no se pudo escribir {destination}: {exc}") from exc

    if total == 0:
        temporary.unlink(missing_ok=True)
        raise DownloadError(f"respuesta vacía: {url}")
    if not is_probably_fits(temporary):
        temporary.unlink(missing_ok=True)
        raise DownloadError(f"el contenido no parece un FITS: {url}")

    os.replace(temporary, destination)
    if metadata:
        from .manifest import write_json_atomic

        write_json_atomic(metadata, destination.with_suffix(destination.suffix + ".http.json"))
    return destination


def download_to_file(
    client: httpx.Client,
    url: str,
    destination: Path,
    *,
    max_bytes: int,
    budget: DownloadBudget | None = None,
    chunk_size: int = 1024 * 1024,
    attempts: int = 1,
    backoff: float = 0.0,
    space_check: Callable[[int], None] | None = None,
    allowed_hosts: tuple[str, ...] | None = None,
) -> Path:
    """Descarga en streaming y publica el archivo solo si es válido.

    Un HTML de error nunca se guarda como ``.fits``: se valida la cabecera
    antes de renombrar de forma atómica. Los fallos transitorios se reintentan
    con backoff; agotar el presupuesto no se reintenta.
    """

    if allowed_hosts is not None:
        validate_remote_url(url, allowed_hosts)
    last_error: DownloadError | None = None
    for attempt in range(max(1, attempts)):
        check_deadline()
        remaining = remaining_seconds()
        acquired = _SLOTS.acquire(timeout=remaining) if remaining is not None else _SLOTS.acquire()
        if not acquired:
            raise DeadlineExceeded("presupuesto temporal agotado esperando descarga")
        try:
            try:
                return _download_once(
                    client, url, destination, max_bytes=max_bytes,
                    budget=budget, chunk_size=chunk_size, space_check=space_check,
                )
            finally:
                _SLOTS.release()
        except DownloadError as exc:
            last_error = exc
            exhausted = "presupuesto" in str(exc)
            if exhausted or not exc.transient or attempt + 1 >= attempts:
                raise
            wait_retry(retry_delay(exc.retry_after, backoff * (2**attempt)))
    raise last_error or DownloadError(f"descarga fallida: {url}")
