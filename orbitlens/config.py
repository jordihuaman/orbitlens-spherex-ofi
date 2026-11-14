"""Configuración del servicio, con valores por defecto explícitos.

Los valores son decisiones de OrbitLens (no requisitos de NASA). Se pueden
sobrescribir por entorno para despliegue sin tocar el código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

PIPELINE_VERSION = "0.1.3"
SCHEMA_VERSION = 1

# Colecciones vigentes tras la revisión de noviembre de 2026 (DR1 + QR3).
DEFAULT_COLLECTIONS = (
    "spherex_dr1",
    "spherex_qr3",
    "spherex_dr1_deep",
    "spherex_qr3_deep",
)

DEFAULT_SIA_URL = "https://irsa.ipac.caltech.edu/SIA"
DEFAULT_PIXEL_SCALE_ARCSEC = 6.15


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - configuración inválida
        raise ValueError(f"{name} debe ser un entero, se recibió {raw!r}") from exc


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as exc:  # pragma: no cover - configuración inválida
        raise ValueError(f"{name} debe ser un número, se recibió {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Parámetros operativos del servicio."""

    data_dir: Path = Path("data")
    sia_url: str = DEFAULT_SIA_URL
    collections: tuple[str, ...] = DEFAULT_COLLECTIONS

    # Selección temporal
    default_frames: int = 12
    min_frames: int = 3
    max_frames: int = 16
    max_candidates: int = 64
    search_maxrec: int = 1000

    # Rejilla de salida
    pixel_scale_arcsec: float = DEFAULT_PIXEL_SCALE_ARCSEC
    cutout_margin: float = 1.5
    min_valid_fraction: float = 0.70

    # Red y cuotas
    connect_timeout_s: float = 10.0
    read_timeout_s: float = 120.0
    retry_attempts: int = 3
    retry_backoff_s: float = 1.0
    max_download_bytes: int = 100 * 1024 * 1024
    max_job_download_bytes: int = 512 * 1024 * 1024
    cache_ttl_hours: int = 24
    allowed_cutout_hosts: tuple[str, ...] = ("irsa.ipac.caltech.edu",)
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

    # Cola
    max_workers: int = 3
    max_active_jobs: int = 32

    def __post_init__(self) -> None:
        if self.min_frames < 2:
            raise ValueError("min_frames debe ser >= 2")
        if not (self.min_frames <= self.default_frames <= self.max_frames):
            raise ValueError("debe cumplirse min_frames <= default_frames <= max_frames")
        if not (0 < self.min_valid_fraction <= 1):
            raise ValueError("min_valid_fraction debe estar en (0, 1]")
        if self.pixel_scale_arcsec <= 0:
            raise ValueError("pixel_scale_arcsec debe ser positivo")
        if self.cutout_margin < 1:
            raise ValueError("cutout_margin debe ser >= 1")
        if self.retry_attempts < 1:
            raise ValueError("retry_attempts debe ser >= 1")
        if self.retry_backoff_s < 0:
            raise ValueError("retry_backoff_s debe ser >= 0")

    @classmethod
    def from_env(cls) -> Settings:
        """Construye la configuración leyendo variables ``ORBITLENS_*``."""

        base = cls()
        overrides: dict[str, object] = {}

        if raw := os.environ.get("ORBITLENS_DATA_DIR"):
            overrides["data_dir"] = Path(raw)
        if raw := os.environ.get("ORBITLENS_SIA_URL"):
            overrides["sia_url"] = raw
        if raw := os.environ.get("ORBITLENS_COLLECTIONS"):
            overrides["collections"] = _split_csv(raw)
        if raw := os.environ.get("ORBITLENS_ALLOWED_HOSTS"):
            overrides["allowed_cutout_hosts"] = _split_csv(raw)
        if raw := os.environ.get("ORBITLENS_CORS_ORIGINS"):
            overrides["cors_origins"] = _split_csv(raw)

        for name, field_name in (
            ("ORBITLENS_MAX_FRAMES", "max_frames"),
            ("ORBITLENS_DEFAULT_FRAMES", "default_frames"),
            ("ORBITLENS_MAX_CANDIDATES", "max_candidates"),
            ("ORBITLENS_SEARCH_MAXREC", "search_maxrec"),
            ("ORBITLENS_MAX_WORKERS", "max_workers"),
            ("ORBITLENS_MAX_ACTIVE_JOBS", "max_active_jobs"),
            ("ORBITLENS_CACHE_TTL_HOURS", "cache_ttl_hours"),
            ("ORBITLENS_RETRY_ATTEMPTS", "retry_attempts"),
        ):
            if os.environ.get(name) is not None:
                overrides[field_name] = _env_int(name, int(getattr(base, field_name)))

        for name, field_name in (
            ("ORBITLENS_PIXEL_SCALE_ARCSEC", "pixel_scale_arcsec"),
            ("ORBITLENS_MIN_VALID_FRACTION", "min_valid_fraction"),
            ("ORBITLENS_CUTOUT_MARGIN", "cutout_margin"),
            ("ORBITLENS_READ_TIMEOUT_S", "read_timeout_s"),
            ("ORBITLENS_CONNECT_TIMEOUT_S", "connect_timeout_s"),
            ("ORBITLENS_RETRY_BACKOFF_S", "retry_backoff_s"),
        ):
            if os.environ.get(name) is not None:
                overrides[field_name] = _env_float(name, float(getattr(base, field_name)))

        return replace(base, **overrides)
