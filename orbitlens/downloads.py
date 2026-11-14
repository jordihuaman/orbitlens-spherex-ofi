"""Descarga acotada de recortes FITS, con presupuesto y validación básica."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

__all__ = ["DownloadError", "DownloadBudget", "download_to_file", "is_probably_fits"]


class DownloadError(RuntimeError):
    """Fallo de descarga, tamaño excesivo o contenido no FITS."""


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
) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")

    total = 0
    try:
        with client.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_bytes(chunk_size):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise DownloadError(
                            f"respuesta mayor que {max_bytes} bytes: {url}"
                        )
                    if budget is not None:
                        budget.consume(len(chunk))
                    handle.write(chunk)
    except httpx.HTTPError as exc:
        temporary.unlink(missing_ok=True)
        raise DownloadError(f"descarga fallida {url}: {exc}") from exc
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
) -> Path:
    """Descarga en streaming y publica el archivo solo si es válido.

    Un HTML de error nunca se guarda como ``.fits``: se valida la cabecera
    antes de renombrar de forma atómica. Los fallos transitorios se reintentan
    con backoff; agotar el presupuesto no se reintenta.
    """

    last_error: DownloadError | None = None
    for attempt in range(max(1, attempts)):
        try:
            return _download_once(
                client,
                url,
                destination,
                max_bytes=max_bytes,
                budget=budget,
                chunk_size=chunk_size,
            )
        except DownloadError as exc:
            last_error = exc
            exhausted = "presupuesto" in str(exc)
            if exhausted or attempt + 1 >= attempts:
                raise
            time.sleep(backoff * (2**attempt))
    raise last_error or DownloadError(f"descarga fallida: {url}")
