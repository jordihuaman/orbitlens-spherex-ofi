"""Configuración del servicio, con valores por defecto explícitos.

Los valores son decisiones de OrbitLens (no requisitos de NASA). Se pueden
sobrescribir por entorno para despliegue sin tocar el código.
"""

from __future__ import annotations

import ipaddress
import math
import os
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import urlsplit

PIPELINE_VERSION = "0.1.6"
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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    if raw.lower() in {"1", "true", "yes"}:
        return True
    if raw.lower() in {"0", "false", "no"}:
        return False
    raise ValueError(f"{name} debe ser true/false")


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
    empty_cache_ttl_s: int = 60
    allowed_cutout_hosts: tuple[str, ...] = ("irsa.ipac.caltech.edu",)
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

    # Cola
    max_workers: int = 3
    max_active_jobs: int = 32
    max_active_per_ip: int = 2
    searches_per_minute: int = 10
    trusted_proxies: tuple[str, ...] = ()
    job_timeout_s: float = 600.0
    max_sia_bytes: int = 16 * 1024 * 1024
    storage_max_bytes: int = 2 * 1024 * 1024 * 1024
    min_free_disk_bytes: int = 64 * 1024 * 1024

    # Perfil HTTP: no implica certificación ni sustituye TLS/firewall del host.
    production: bool = False
    public_origin: str | None = None
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "[::1]", "testserver")
    enable_docs: bool = False
    max_request_bytes: int = 16 * 1024
    request_body_timeout_s: float = 10.0
    http_requests_per_minute: int = 600
    http_burst: int = 120
    max_http_clients: int = 2048
    security_contact: str | None = None

    def __post_init__(self) -> None:
        for name in ("connect_timeout_s", "read_timeout_s", "job_timeout_s", "pixel_scale_arcsec", "request_body_timeout_s"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} debe ser finito y positivo")
        for name in ("max_workers", "max_active_jobs", "max_active_per_ip", "searches_per_minute",
                     "max_download_bytes", "max_job_download_bytes", "max_sia_bytes", "max_candidates",
                     "storage_max_bytes", "max_request_bytes", "http_requests_per_minute", "http_burst", "max_http_clients"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} debe ser positivo")
        for proxy in self.trusted_proxies:
            ipaddress.ip_network(proxy)
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
        if not math.isfinite(self.retry_backoff_s) or self.retry_backoff_s < 0:
            raise ValueError("retry_backoff_s debe ser >= 0")
        if self.empty_cache_ttl_s < 0:
            raise ValueError("empty_cache_ttl_s debe ser >= 0")
        if self.min_free_disk_bytes < 0:
            raise ValueError("min_free_disk_bytes debe ser >= 0")
        if not self.allowed_hosts or any("*" in value or "/" in value or "@" in value for value in self.allowed_hosts):
            raise ValueError("allowed_hosts requiere hosts concretos, sin comodines ni rutas")
        for origin in (*self.cors_origins, *((self.public_origin,) if self.public_origin else ())):
            parts = urlsplit(origin)
            if (parts.scheme not in {"https", "http"} or not parts.hostname or parts.path
                    or parts.query or parts.fragment or parts.username or parts.password):
                raise ValueError("los orígenes deben ser scheme://host[:puerto], sin ruta ni credenciales")
            if self.production and parts.scheme != "https":
                raise ValueError("producción requiere orígenes HTTPS")
        if self.production:
            if not self.public_origin or self.enable_docs:
                raise ValueError("producción requiere public_origin HTTPS y documentación interactiva desactivada")
            if urlsplit(self.public_origin).hostname not in {value.strip("[]").lower() for value in self.allowed_hosts}:
                raise ValueError("el host de public_origin debe figurar en allowed_hosts")
        if self.security_contact and ("\r" in self.security_contact or "\n" in self.security_contact
                                      or not self.security_contact.startswith(("mailto:", "https://"))):
            raise ValueError("security_contact requiere mailto: o https: sin saltos de línea")

    @classmethod
    def from_env(cls) -> Settings:
        """Construye la configuración leyendo variables ``ORBITLENS_*``."""

        base = cls()
        overrides: dict[str, object] = {}
        overrides["production"] = _env_bool("ORBITLENS_PRODUCTION", base.production)
        overrides["enable_docs"] = _env_bool("ORBITLENS_ENABLE_DOCS", base.enable_docs)
        if overrides["production"] and "ORBITLENS_CORS_ORIGINS" not in os.environ:
            overrides["cors_origins"] = ()
        for name, field_name in (("ORBITLENS_PUBLIC_ORIGIN", "public_origin"),
                                 ("ORBITLENS_SECURITY_CONTACT", "security_contact")):
            if os.environ.get(name):
                overrides[field_name] = os.environ[name]
        if raw := os.environ.get("ORBITLENS_ALLOWED_WEB_HOSTS"):
            overrides["allowed_hosts"] = _split_csv(raw)

        if raw := os.environ.get("ORBITLENS_DATA_DIR"):
            overrides["data_dir"] = Path(raw)
        if raw := os.environ.get("ORBITLENS_SIA_URL"):
            overrides["sia_url"] = raw
        if raw := os.environ.get("ORBITLENS_COLLECTIONS"):
            overrides["collections"] = _split_csv(raw)
        if raw := os.environ.get("ORBITLENS_ALLOWED_HOSTS"):
            overrides["allowed_cutout_hosts"] = _split_csv(raw)
        if "ORBITLENS_CORS_ORIGINS" in os.environ:
            overrides["cors_origins"] = _split_csv(os.environ["ORBITLENS_CORS_ORIGINS"])
        if raw := os.environ.get("ORBITLENS_TRUSTED_PROXIES"):
            overrides["trusted_proxies"] = _split_csv(raw)

        for name, field_name in (
            ("ORBITLENS_MAX_FRAMES", "max_frames"),
            ("ORBITLENS_DEFAULT_FRAMES", "default_frames"),
            ("ORBITLENS_MAX_CANDIDATES", "max_candidates"),
            ("ORBITLENS_SEARCH_MAXREC", "search_maxrec"),
            ("ORBITLENS_MAX_WORKERS", "max_workers"),
            ("ORBITLENS_MAX_ACTIVE_JOBS", "max_active_jobs"),
            ("ORBITLENS_CACHE_TTL_HOURS", "cache_ttl_hours"),
            ("ORBITLENS_EMPTY_CACHE_TTL_S", "empty_cache_ttl_s"),
            ("ORBITLENS_RETRY_ATTEMPTS", "retry_attempts"),
            ("ORBITLENS_MAX_ACTIVE_PER_IP", "max_active_per_ip"),
            ("ORBITLENS_SEARCHES_PER_MINUTE", "searches_per_minute"),
            ("ORBITLENS_MAX_DOWNLOAD_BYTES", "max_download_bytes"),
            ("ORBITLENS_MAX_JOB_DOWNLOAD_BYTES", "max_job_download_bytes"),
            ("ORBITLENS_MAX_SIA_BYTES", "max_sia_bytes"),
            ("ORBITLENS_STORAGE_MAX_BYTES", "storage_max_bytes"),
            ("ORBITLENS_MIN_FREE_DISK_BYTES", "min_free_disk_bytes"),
            ("ORBITLENS_MAX_REQUEST_BYTES", "max_request_bytes"),
            ("ORBITLENS_HTTP_REQUESTS_PER_MINUTE", "http_requests_per_minute"),
            ("ORBITLENS_HTTP_BURST", "http_burst"),
            ("ORBITLENS_MAX_HTTP_CLIENTS", "max_http_clients"),
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
            ("ORBITLENS_JOB_TIMEOUT_S", "job_timeout_s"),
            ("ORBITLENS_REQUEST_BODY_TIMEOUT_S", "request_body_timeout_s"),
        ):
            if os.environ.get(name) is not None:
                overrides[field_name] = _env_float(name, float(getattr(base, field_name)))

        return replace(base, **overrides)
