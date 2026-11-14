"""Orquestación: búsqueda IRSA → recortes → pipeline → manifiesto.

La clase ``SearchService`` concentra efectos externos. Las decisiones puras
(selección temporal, clasificación de estado, construcción del manifiesto) se
exponen como funciones para poder probarlas sin red.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

from .cache import FileCache
from .config import PIPELINE_VERSION, SCHEMA_VERSION, Settings
from .downloads import DownloadBudget, download_to_file
from .execution import DeadlineExceeded, check_deadline, execution_budget
from .irsa_client import SearchOutcome, SiaRecord, search
from .jobs import Job
from .manifest import sha256_file, utc_now_iso, validate_result_files, write_json_atomic
from .pipeline import (
    ProcessedFrame,
    SpherexImage,
    build_target_wcs,
    compute_stretch_limits,
    read_spherex_image,
    render_rgba,
    reproject_frame,
    write_derived_fits,
    write_png,
)
from .storage import KeyedLocks, StorageError, StorageManager

__all__ = [
    "SearchService",
    "select_spread",
    "classify_status",
    "sanitize_name",
    "mjd_to_iso",
]

MASK_POLICY_VERSION = "1.0"


def normalize_detector(value: str | int | None) -> str | None:
    text = str(value if value is not None else "").strip()
    if text in {"1", "2", "3", "4", "5", "6"}:
        return f"D{text}"
    match = re.fullmatch(r"(?:SPHEREx-)?(D[1-6])", text, re.IGNORECASE)
    return match.group(1).upper() if match else None


def record_detector(record: SiaRecord) -> str | None:
    values = {value for raw in (record.bandpass, record.instrument)
              if (value := normalize_detector(raw)) is not None}
    return next(iter(values)) if len(values) == 1 else None


def select_detector(records: list[SiaRecord], requested: str) -> tuple[list[SiaRecord], str | None]:
    """Un solo detector; auto elige más exposiciones (desempate D1–D6).

    Metadatos desconocidos o contradictorios se excluyen. Nunca sustituye
    una selección explícita por todos los detectores.
    """
    groups: dict[str, list[SiaRecord]] = {}
    for record in records:
        if detector := record_detector(record):
            groups.setdefault(detector, []).append(record)
    chosen = normalize_detector(requested)
    if requested.lower() == "auto":
        chosen = min(groups, key=lambda key: (-len(groups[key]), key)) if groups else None
    return groups.get(chosen, []) if chosen else [], chosen


def sanitize_name(value: str, *, fallback: str = "frame") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return (cleaned or fallback)[:80]


def mjd_to_iso(mjd: float | None) -> str | None:
    if mjd is None or not math.isfinite(mjd):
        return None
    try:
        from astropy.time import Time

        return Time(mjd, format="mjd", scale="utc").isot + "Z"
    except Exception:  # pragma: no cover - depende de datos externos
        return None


def select_spread(records: list[SiaRecord], limit: int) -> list[SiaRecord]:
    """Selecciona hasta ``limit`` registros repartidos en el intervalo temporal."""

    if limit < 1:
        return []
    ordered = sorted(records, key=lambda record: record.sort_key)
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return ordered[:1]
    indices = [
        round(index * (len(ordered) - 1) / (limit - 1)) for index in range(limit)
    ]
    selected: list[SiaRecord] = []
    seen: set[int] = set()
    for index in indices:
        if index not in seen:
            seen.add(index)
            selected.append(ordered[index])
    return selected


def classify_status(
    *, processed: int, min_frames: int, had_failures: bool, overflow: bool
) -> str:
    if processed == 0:
        return "error"
    if processed < min_frames or had_failures or overflow:
        return "partial"
    return "ready"


@dataclass
class _PreparedFrame:
    record: SiaRecord
    image: SpherexImage
    processed: ProcessedFrame


class SearchService:
    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.Client | None = None,
        search_fn: Callable[..., SearchOutcome] = search,
        download_fn: Callable[..., Path] = download_to_file,
    ) -> None:
        self.settings = settings
        self.cache = FileCache(settings.data_dir / "cache")
        self.results_dir = settings.data_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._owns_client = client is None
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(
                settings.read_timeout_s, connect=settings.connect_timeout_s
            ),
            follow_redirects=True,
        )
        self._search = search_fn
        self._download = download_fn
        self.storage = StorageManager(settings.data_dir, settings.storage_max_bytes, settings.min_free_disk_bytes)
        self._locks = KeyedLocks()
        self.search_provenance = {"method": "sia"}

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    # ------------------------------------------------------------------ cache
    def _search_cache_key(
        self, ra_deg: float, dec_deg: float, fov_arcmin: float
    ) -> str:
        return self.cache.key(
            "sia",
            self.settings.sia_url,
            self.settings.collections,
            round(ra_deg, 6),
            round(dec_deg, 6),
            round(fov_arcmin, 3),
            self.settings.search_maxrec,
        )

    def _read_search_cache(self, key: str, *, require_fresh: bool) -> dict | None:
        path = self.cache.path("sia", key, "search.json")
        if not path.is_file():
            return None
        try:
            cached = self.cache.read_json("sia", key, "search.json")
            if not isinstance(cached, dict) or not isinstance(cached.get("records"), list):
                return None
            ttl = (self.settings.cache_ttl_hours if cached["records"]
                   else self.settings.empty_cache_ttl_s / 3600)
            if require_fresh and not self.cache.is_fresh("sia", key, "search.json", ttl):
                return None
            return cached
        except (OSError, json.JSONDecodeError):
            return None

    def _write_search_cache(
        self,
        key: str,
        outcome: SearchOutcome,
        *,
        queried_at: str,
    ) -> None:
        self.cache.write_json(
            "sia",
            key,
            "search.json",
            {
                "queried_at": queried_at,
                "collections": outcome.collections,
                "overflow": outcome.overflow,
                "warnings": outcome.warnings,
                "records": [asdict(record) for record in outcome.records],
            },
        )

    # ---------------------------------------------------------------- búsqueda
    def _find_records(
        self, job: Job, ra_deg: float, dec_deg: float, fov_arcmin: float
    ) -> tuple[SearchOutcome, str, bool]:
        key = self._search_cache_key(ra_deg, dec_deg, fov_arcmin)
        with self._locks.hold(("sia", key)):
            return self._find_records_locked(job, ra_deg, dec_deg, fov_arcmin)

    def _find_records_locked(
        self, job: Job, ra_deg: float, dec_deg: float, fov_arcmin: float
    ) -> tuple[SearchOutcome, str, bool]:
        key = self._search_cache_key(ra_deg, dec_deg, fov_arcmin)
        cached = self._read_search_cache(key, require_fresh=True)
        if cached is not None:
            outcome = SearchOutcome(
                records=[SiaRecord(**item) for item in cached["records"]],
                warnings=list(cached.get("warnings", [])),
                collections=list(cached.get("collections", [])),
                overflow=bool(cached.get("overflow", False)),
            )
            return outcome, str(cached.get("queried_at", "")), True

        queried_at = utc_now_iso()
        outcome = self._search(
            self.client,
            self.settings,
            ra_deg,
            dec_deg,
            fov_arcmin,
            collections=self.settings.collections,
        )

        failed = sum(
            1
            for collection in outcome.collections
            if any(
                warning.startswith(f"SIA {collection}:")
                for warning in outcome.warnings
            )
        )
        all_failed = bool(outcome.collections) and failed == len(outcome.collections)
        if all_failed:
            stale = self._read_search_cache(key, require_fresh=False)
            if stale is not None and stale["records"]:
                job.add_warning(
                    "IRSA no respondió; se usa una consulta anterior en caché. "
                    "La secuencia puede no reflejar los datos más recientes."
                )
                outcome = SearchOutcome(
                    records=[SiaRecord(**item) for item in stale["records"]],
                    warnings=[*stale.get("warnings", []), *outcome.warnings],
                    collections=list(stale.get("collections", [])),
                    overflow=bool(stale.get("overflow", False)),
                )
                return outcome, str(stale.get("queried_at", "")), True
            raise RuntimeError(
                "todas las colecciones IRSA fallaron: "
                + "; ".join(outcome.warnings[:3])
            )

        # No congelar errores de dependencia como si fueran vacíos confirmados.
        if not failed:
            self._write_search_cache(key, outcome, queried_at=queried_at)
        return outcome, queried_at, False

    # ------------------------------------------------------------------ frames
    def _prepare_frame(
        self,
        record: SiaRecord,
        ra_deg: float,
        dec_deg: float,
        fov_arcmin: float,
        target_wcs,
        shape: tuple[int, int],
        budget: DownloadBudget,
    ) -> _PreparedFrame:
        size_deg = min(5.0, fov_arcmin / 60.0 * self.settings.cutout_margin)
        cutout_url = record.cutout_url(
            ra_deg,
            dec_deg,
            size_deg,
            allowed_hosts=self.settings.allowed_cutout_hosts,
        )
        cache_key = self.cache.key(
            "cutout",
            record.access_url,
            record.obs_id,
            round(ra_deg, 6),
            round(dec_deg, 6),
            round(size_deg, 6),
        )
        filename = f"{sanitize_name(record.obs_id, fallback='cutout')}.fits"
        raw_path = self.cache.path("cutout", cache_key, filename)
        with self._locks.hold(("cutout", cache_key)):
            checksum_path = raw_path.with_suffix(".integrity.json")
            if raw_path.is_file() and checksum_path.is_file():
                try:
                    integrity = json.loads(checksum_path.read_text(encoding="utf-8"))
                    intact = (raw_path.stat().st_size == integrity["bytes"]
                              and sha256_file(raw_path) == integrity["sha256"])
                except (OSError, ValueError, TypeError, KeyError):
                    intact = False
                if not intact:
                    raw_path.unlink()
                    checksum_path.unlink(missing_ok=True)
            if not raw_path.is_file():
                self._download(
                    self.client, cutout_url, raw_path,
                    max_bytes=self.settings.max_download_bytes, budget=budget,
                    attempts=self.settings.retry_attempts, backoff=self.settings.retry_backoff_s,
                    space_check=self.storage.ensure_space,
                )
            if not checksum_path.is_file():
                write_json_atomic({"bytes": raw_path.stat().st_size, "sha256": sha256_file(raw_path)}, checksum_path)
            os.utime(raw_path, (time.time(), raw_path.stat().st_mtime))

        image = read_spherex_image(raw_path, target=(ra_deg, dec_deg))
        if normalize_detector(image.detector) is None or not image.version or not image.bunit:
            raise ValueError("FITS sin detector reconocible, VERSION o BUNIT")
        if image.header.get("OBSID") and str(image.header["OBSID"]).strip() != record.obs_id:
            raise ValueError("el OBSID del FITS contradice la selección SIA")
        if "MJD-OBS" in image.header and record.t_min is not None:
            actual_time = float(image.header["MJD-OBS"])
            if not math.isfinite(actual_time) or abs(actual_time - record.t_min) > 1e-5:
                raise ValueError("MJD-OBS del FITS contradice el tiempo SIA")
        if image.valid_fraction < self.settings.min_valid_fraction:
            raise ValueError(
                f"cobertura válida {image.valid_fraction:.1%} < "
                f"{self.settings.min_valid_fraction:.0%}"
            )
        processed = reproject_frame(image, target_wcs, shape)
        if processed.valid_fraction < self.settings.min_valid_fraction:
            raise ValueError(
                f"cobertura válida de salida {processed.valid_fraction:.1%} < "
                f"{self.settings.min_valid_fraction:.0%}"
            )
        return _PreparedFrame(record=record, image=image, processed=processed)

    # ------------------------------------------------------------------ público
    def run(self, job: Job, request: dict[str, object]) -> None:
        with execution_budget(self.settings.job_timeout_s):
            with self.storage.activity(), self._locks.hold(("request", json.dumps(request, sort_keys=True))):
                self._run(job, request)

    def _run(self, job: Job, request: dict[str, object]) -> None:
        ra_deg = float(request["ra_deg"])
        dec_deg = float(request["dec_deg"])
        fov_arcmin = float(request["fov_arcmin"])
        requested_frames = int(request["frames"])
        detector = str(request.get("detector", "auto"))

        job.update(phase="searching")
        outcome, queried_at, from_cache = self._find_records(
            job, ra_deg, dec_deg, fov_arcmin
        )
        for warning in outcome.warnings:
            job.add_warning(warning)
        failed_collections = [collection for collection in outcome.collections
                              if any(warning.startswith(f"SIA {collection}:")
                                     for warning in outcome.warnings)]
        job.set_counts(
            collections_queried=len(outcome.collections),
            records_found=len(outcome.records),
        )
        if from_cache:
            job.add_warning(f"consulta SIA servida desde caché ({queried_at})")

        candidates = [
            record
            for record in outcome.records
            if record.dataproduct_type is None
            or record.dataproduct_type.lower() == "image"
        ]
        without_time = sum(1 for record in candidates if record.t_min is None)
        if without_time:
            job.add_warning(
                f"{without_time} registros sin t_min se excluyen de la secuencia temporal"
            )
            candidates = [record for record in candidates if record.t_min is not None]

        candidates, selected_detector = select_detector(candidates, detector)
        unique: dict[str, SiaRecord] = {}
        for record in candidates:
            unique.setdefault(record.obs_id, record)
        duplicates = len(candidates) - len(unique)
        candidates = list(unique.values())
        if duplicates:
            job.add_warning(f"{duplicates} exposiciones duplicadas excluidas por OBSID y detector")
        job.add_warning(
            f"Detector solicitado: {detector}; seleccionado: {selected_detector or 'ninguno'}. "
            "Un mismo detector no garantiza compatibilidad espectral."
        )
        check_deadline()
        limit = min(requested_frames, self.settings.max_frames)
        selected = select_spread(candidates, limit)
        job.set_counts(selected=len(selected), candidates=len(candidates))

        if not selected:
            if failed_collections:
                job.update(status="error", phase=None, result_id=None,
                           error="consulta incompleta: no se puede confirmar ausencia de imágenes")
                return
            job.update(status="empty", phase=None, result_id=None)
            job.add_warning(
                "la consulta terminó sin imágenes utilizables para este campo; "
                "no implica ausencia física del objeto"
            )
            return

        target_wcs, width, height = build_target_wcs(
            ra_deg,
            dec_deg,
            fov_arcmin,
            pixel_scale_arcsec=self.settings.pixel_scale_arcsec,
        )
        shape = (height, width)

        job.update(phase="downloading")
        budget = DownloadBudget(self.settings.max_job_download_bytes)
        prepared: list[_PreparedFrame] = []
        failures: list[str] = []
        # Primero repartir épocas, después intentar sustitutos dentro de cuota.
        remaining = [record for record in candidates if record not in selected]
        attempts = (selected + select_spread(remaining, len(remaining)))[:self.settings.max_candidates]
        attempted = 0
        for index, record in enumerate(attempts, start=1):
            check_deadline()
            attempted = index
            try:
                prepared.append(
                    self._prepare_frame(
                        record, ra_deg, dec_deg, fov_arcmin, target_wcs, shape, budget
                    )
                )
                actual = normalize_detector(prepared[-1].image.detector)
                if actual is not None and actual != selected_detector:
                    prepared.pop()
                    raise ValueError("el detector del FITS contradice la selección SIA")
            except (DeadlineExceeded, StorageError):
                raise
            except Exception as exc:  # noqa: BLE001 - un frame no debe tumbar el trabajo
                failures.append(f"{record.obs_id}: {exc}")
                job.add_warning(f"frame descartado {record.obs_id}: {exc}")
            job.set_counts(
                attempted=index,
                processed=len(prepared),
                failed=len(failures),
            )
            if len(prepared) >= limit or budget.used > budget.max_bytes:
                break

        if not prepared:
            job.update(status="error", phase=None, result_id=None)
            job.add_warning("ningún frame pudo descargarse y procesarse")
            return

        job.update(phase="processing")
        prepared.sort(key=lambda item: item.record.sort_key)
        vmin, vmax = compute_stretch_limits([frame.processed for frame in prepared])
        status = classify_status(
            processed=len(prepared), min_frames=self.settings.min_frames,
            had_failures=bool(failures or failed_collections), overflow=outcome.overflow,
        )

        selection_payload = [
            [frame.record.obs_id, frame.record.collection, frame.record.t_min,
             sha256_file(frame.image.path)]
            for frame in prepared
        ]
        identity = {
            "request": request,
            "collections": self.settings.collections,
            "selection": selection_payload,
            "pipeline_version": PIPELINE_VERSION,
            "mask_policy": MASK_POLICY_VERSION,
            "search_incomplete": [failed_collections, outcome.overflow],
            "provenance": self.search_provenance,
            "grid": [round(ra_deg, 6), round(dec_deg, 6), fov_arcmin, width, height],
        }
        result_id = hashlib.sha256(
            json.dumps(identity, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        result_dir = self.results_dir / result_id

        manifest_path = result_dir / "manifest.json"
        if manifest_path.is_file():
            try:
                existing = json.loads(manifest_path.read_text(encoding="utf-8"))
                validate_result_files(result_dir, existing)
                job.update(
                    status=status,
                    phase=None,
                    result_id=result_id,
                )
                job.set_counts(
                    attempted=attempted,
                    processed=len(existing["frames"]),
                    failed=len(failures),
                )
                job.add_warning("resultado reutilizado desde caché (mismo conjunto de entrada)")
                return
            except (OSError, ValueError, json.JSONDecodeError):
                pass

        frames_dir = result_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_entries: list[dict[str, object]] = []
        file_entries: list[dict[str, object]] = []

        for index, prepared_frame in enumerate(prepared, start=1):
            check_deadline()
            record = prepared_frame.record
            processed = prepared_frame.processed
            image = prepared_frame.image
            frame_id = f"{index:02d}_{sanitize_name(record.obs_id)}"
            png_rel = f"frames/{frame_id}.png"
            fits_rel = f"frames/{frame_id}.fits"
            original_rel = f"frames/{frame_id}-original.fits"
            original_path = result_dir / original_rel
            self.storage.ensure_space(image.path.stat().st_size + width * height * 8)
            shutil.copyfile(image.path, original_path)

            rgba = render_rgba(processed, vmin, vmax)
            png_path = result_dir / png_rel
            write_png(rgba, png_path)
            fits_path = result_dir / fits_rel
            write_derived_fits(
                processed.data,
                target_wcs,
                fits_path,
                metadata={
                    "OBSID": record.obs_id,
                    "COLLECT": record.collection,
                    "BUNIT": image.bunit,
                    "LAMBDA": image.lambda_um,
                    "BANDWID": image.bandwidth_um,
                },
            )

            frame_entry = {
                "frame_id": frame_id,
                "png": png_rel,
                "fits": fits_rel,
                "original_fits": original_rel,
                "access_url": record.access_url,
                "cutout_url": record.cutout_url(
                    ra_deg, dec_deg, min(5.0, fov_arcmin / 60 * self.settings.cutout_margin),
                    allowed_hosts=self.settings.allowed_cutout_hosts,
                ),
                "bunit": image.bunit,
                "mask_definitions": image.flag_definitions.bits,
                "obs_id": record.obs_id,
                "collection": record.collection,
                "detector": normalize_detector(image.detector) or selected_detector,
                "version": image.version,
                "time": {
                    "t_min_mjd": record.t_min,
                    "t_max_mjd": record.t_max,
                    "label": mjd_to_iso(record.t_min),
                },
                "lambda_um": image.lambda_um,
                "bandwidth_um": image.bandwidth_um,
                "valid_fraction": round(processed.valid_fraction, 6),
                "center_valid": processed.center_valid,
                "warnings": list(image.warnings),
            }
            http_metadata = image.path.with_suffix(image.path.suffix + ".http.json")
            if http_metadata.is_file():
                try:
                    frame_entry["http_metadata"] = json.loads(http_metadata.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    pass
            frame_entries.append(frame_entry)

            for suffix, kind, relative, path in (
                ("png", "png", png_rel, png_path),
                ("fits", "fits", fits_rel, fits_path),
                ("original", "fits", original_rel, original_path),
            ):
                file_entries.append(
                    {
                        "id": f"{frame_id}-{suffix}",
                        "kind": kind,
                        "path": relative,
                        "sha256": sha256_file(path),
                        "bytes": path.stat().st_size,
                    }
                )

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "code_commit": os.environ.get("ORBITLENS_CODE_COMMIT", "dev"),
            "result_id": result_id,
            "created_at": utc_now_iso(),
            "status": status,
            "request": request,
            "search": {
                **self.search_provenance,
                "queried_at": queried_at,
                "collections": outcome.collections,
                "records_found": len(outcome.records),
                "candidates": len(candidates),
                "duplicate_exposures": duplicates,
                "deduplication": "OBSID dentro del detector elegido; primera fila devuelta",
                "selected": len(selected),
                "attempted": attempted,
                "processed": len(prepared),
                "failures": failures,
                "failed_collections": failed_collections,
                "overflow": outcome.overflow,
                "from_cache": from_cache,
                "selection": "distribución uniforme sobre el intervalo disponible",
                "detector_requested": detector,
                "detector_selected": selected_detector,
            },
            "grid": {
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "fov_arcmin": fov_arcmin,
                "width": width,
                "height": height,
                "pixel_scale_arcsec": self.settings.pixel_scale_arcsec,
                "projection": "RA---TAN/DEC--TAN, norte arriba",
            },
            "processing": {
                "mask_policy_version": MASK_POLICY_VERSION,
                "min_valid_fraction": self.settings.min_valid_fraction,
                "background": "no sustraído; incluye fondo zodiacal",
                "stretch": {
                    "mode": "asinh",
                    "vmin": vmin,
                    "vmax": vmax,
                    "softening": 0.05,
                    "scope": "percentiles globales de la secuencia",
                },
                "spectral_policy": "λ y ancho de banda por frame; sin apilar",
            },
            "frames": frame_entries,
            "files": file_entries,
            "warnings": list(job.public()["warnings"]),
        }
        validate_result_files(result_dir, manifest)
        check_deadline()
        write_json_atomic(manifest, manifest_path)

        job.update(status=status, phase=None, result_id=result_id)
        job.set_counts(
            attempted=attempted,
            processed=len(prepared),
            failed=len(failures),
        )
