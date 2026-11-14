"""Cliente mínimo del servicio SIA v2 de IRSA para imágenes SPHEREx.

Solo se usa para *descubrir* imágenes y construir URLs de recorte. La descarga
y el procesamiento viven en otros módulos, de modo que las pruebas puedan usar
un cliente falso sin tocar la red.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
import numpy as np
from astropy.io.votable import parse as parse_votable

from .config import Settings

__all__ = [
    "IrsaError",
    "SiaRecord",
    "SearchOutcome",
    "build_sia_params",
    "search_radius_deg",
    "parse_sia_votable",
    "query_collection",
    "search",
]


class IrsaError(RuntimeError):
    """Fallo de consulta o de formato devuelto por IRSA."""


@dataclass(frozen=True)
class SiaRecord:
    obs_id: str
    collection: str
    access_url: str
    bandpass: str | None = None
    t_min: float | None = None
    t_max: float | None = None
    dataproduct_type: str | None = None
    calib_level: int | None = None
    instrument: str | None = None
    target_name: str | None = None
    s_region: str | None = None
    em_min: float | None = None
    em_max: float | None = None
    raw: dict[str, object] = field(default_factory=dict, compare=False, hash=False)

    @property
    def dedupe_key(self) -> tuple[str, str, str | None, float | None]:
        return (self.collection, self.obs_id, self.bandpass, self.t_min)

    @property
    def sort_key(self) -> tuple[float, str]:
        return (self.t_min if self.t_min is not None else math.inf, self.obs_id)

    def cutout_url(
        self,
        ra_deg: float,
        dec_deg: float,
        size_deg: float,
        *,
        allowed_hosts: tuple[str, ...] | None = None,
    ) -> str:
        """Añade ``center`` y ``size`` a la URL on-premises de IRSA.

        No se aplica a URLs S3 ni a orígenes no configurados. El tamaño es el
        ancho completo del recorte, no el radio.
        """

        if not (0 < size_deg <= 5):
            raise IrsaError(f"tamaño de recorte fuera de rango: {size_deg}")

        parts = urlsplit(self.access_url)
        if parts.scheme not in {"http", "https"}:
            raise IrsaError(f"URL de acceso no soportada: {self.access_url!r}")
        if allowed_hosts is not None and parts.hostname not in allowed_hosts:
            raise IrsaError(
                f"host de datos no permitido: {parts.hostname!r}; "
                f"configurados: {allowed_hosts!r}"
            )

        query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in {"center", "size"}
        ]
        query.append(("center", f"{ra_deg:.8f},{dec_deg:.8f}deg"))
        query.append(("size", f"{size_deg:.8f}deg"))
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )


@dataclass
class SearchOutcome:
    records: list[SiaRecord]
    warnings: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)
    overflow: bool = False


def search_radius_deg(fov_arcmin: float, *, margin: float = 1.1) -> float:
    """Semidiagonal del campo cuadrado más un margen de búsqueda."""

    if fov_arcmin <= 0:
        raise ValueError("fov_arcmin debe ser positivo")
    return fov_arcmin * math.sqrt(2.0) / 120.0 * margin


def build_sia_params(
    collection: str,
    ra_deg: float,
    dec_deg: float,
    radius_deg: float,
    *,
    maxrec: int = 1000,
) -> dict[str, str]:
    """Parámetros SIA v2 con POS en grados ICRS."""

    return {
        "COLLECTION": collection,
        "POS": f"CIRCLE {ra_deg:.8f} {dec_deg:.8f} {radius_deg:.8f}",
        "RESPONSEFORMAT": "VOTABLE",
        "MAXREC": str(maxrec),
    }


def _cell(row, names: tuple[str, ...]) -> object | None:
    for name in names:
        try:
            value = row[name]
        except (KeyError, IndexError, TypeError):
            continue
        if value is None:
            return None
        if hasattr(value, "mask") and bool(value.mask):
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8", "replace")
        if isinstance(value, np.generic):
            return value.item()
        return value
    return None


def _as_float(value: object | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _as_int(value: object | None) -> int | None:
    number = _as_float(value)
    return int(number) if number is not None else None


def _as_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _iter_infos(node) -> list[object]:
    infos: list[object] = list(getattr(node, "infos", []) or [])
    for resource in getattr(node, "resources", []) or []:
        infos.extend(_iter_infos(resource))
    for table in getattr(node, "tables", []) or []:
        infos.extend(_iter_infos(table))
    return infos


def _has_overflow(votable) -> bool:
    for info in _iter_infos(votable):
        text = " ".join(
            str(getattr(info, attribute, "") or "")
            for attribute in ("name", "value", "content")
        ).lower()
        if "overflow" in text:
            return True
    return False


def parse_sia_votable(content: bytes) -> tuple[list[SiaRecord], bool]:
    """Convierte una respuesta VOTable en registros y detecta truncamiento."""

    try:
        votable = parse_votable(BytesIO(content))
    except Exception as exc:  # astropy lanza varios tipos según el daño
        raise IrsaError(f"VOTable inválido: {exc}") from exc

    overflow = _has_overflow(votable)
    tables = list(votable.iter_tables())
    if not tables:
        return [], overflow

    try:
        table = tables[0].to_table()
    except Exception as exc:
        raise IrsaError(f"no se pudo materializar la tabla VOTable: {exc}") from exc
    if len(table) == 0:
        return [], overflow

    lower_names = {name.lower(): name for name in table.colnames}
    records: list[SiaRecord] = []
    for row in table:

        def get(*names: str, _row: object = row) -> object | None:
            actual = next(
                (lower_names[name.lower()] for name in names if name.lower() in lower_names),
                None,
            )
            return _cell(_row, (actual,)) if actual else None

        obs_id = _as_text(get("obs_id", "obsid"))
        access_url = _as_text(get("access_url", "accessurl"))
        if not obs_id or not access_url:
            continue

        records.append(
            SiaRecord(
                obs_id=obs_id,
                collection=_as_text(get("obs_collection", "collection")) or "",
                access_url=access_url,
                bandpass=_as_text(get("energy_bandpassname", "bandpass")),
                t_min=_as_float(get("t_min", "tmin")),
                t_max=_as_float(get("t_max", "tmax")),
                dataproduct_type=_as_text(get("dataproduct_type", "dptype")),
                calib_level=_as_int(get("calib_level", "caliblevel")),
                instrument=_as_text(get("instrument_name", "instrument")),
                target_name=_as_text(get("target_name", "targetname")),
                s_region=_as_text(get("s_region", "sregion")),
                em_min=_as_float(get("em_min", "emmin")),
                em_max=_as_float(get("em_max", "emmax")),
            )
        )
    return records, overflow


def _get_with_retries(
    client: httpx.Client,
    url: str,
    params: dict[str, str],
    *,
    collection: str,
    attempts: int,
    backoff: float,
) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            response = client.get(url, params=params)
        except httpx.TransportError as exc:
            last_error = exc
        else:
            if response.status_code < 500:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise IrsaError(f"SIA {collection}: {exc}") from exc
                return response
            last_error = IrsaError(
                f"SIA {collection}: HTTP {response.status_code} del servidor"
            )
        if attempt + 1 < attempts:
            time.sleep(backoff * (2**attempt))
    raise IrsaError(f"SIA {collection}: {last_error}") from last_error


def query_collection(
    client: httpx.Client,
    settings: Settings,
    collection: str,
    ra_deg: float,
    dec_deg: float,
    radius_deg: float,
    *,
    maxrec: int | None = None,
) -> tuple[list[SiaRecord], bool]:
    """Consulta una colección y devuelve ``(registros, overflow)``."""

    params = build_sia_params(
        collection,
        ra_deg,
        dec_deg,
        radius_deg,
        maxrec=maxrec if maxrec is not None else settings.search_maxrec,
    )
    response = _get_with_retries(
        client,
        settings.sia_url,
        params,
        collection=collection,
        attempts=settings.retry_attempts,
        backoff=settings.retry_backoff_s,
    )

    if not response.content:
        raise IrsaError(f"SIA {collection}: respuesta vacía")

    return parse_sia_votable(response.content)


def search(
    client: httpx.Client,
    settings: Settings,
    ra_deg: float,
    dec_deg: float,
    fov_arcmin: float,
    *,
    collections: tuple[str, ...] | None = None,
    maxrec: int | None = None,
) -> SearchOutcome:
    """Consulta todas las colecciones configuradas y deduplica resultados.

    Una colección que falla no oculta las demás: se registra una advertencia y
    el resultado se marca como parcial por quien orquesta la búsqueda.
    """

    radius = search_radius_deg(fov_arcmin)
    outcome = SearchOutcome(records=[])
    seen: set[tuple[str, str, str | None, float | None]] = set()

    for collection in collections or settings.collections:
        outcome.collections.append(collection)
        try:
            records, overflow = query_collection(
                client, settings, collection, ra_deg, dec_deg, radius, maxrec=maxrec
            )
        except IrsaError as exc:
            outcome.warnings.append(str(exc))
            continue

        if overflow:
            outcome.overflow = True
            outcome.warnings.append(
                f"{collection}: resultado truncado (QUERY_STATUS=OVERFLOW); "
                "la muestra no es exhaustiva"
            )

        for record in records:
            if record.dedupe_key in seen:
                continue
            seen.add(record.dedupe_key)
            outcome.records.append(record)

    outcome.records.sort(key=lambda record: record.sort_key)
    return outcome
