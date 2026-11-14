"""Secuencias sin red a partir de MEF IRSA locales con procedencia declarada."""

from __future__ import annotations

import math
from pathlib import Path
from urllib.parse import urlsplit

from astropy.time import Time

from .config import Settings
from .coordinates import validate_dec, validate_ra
from .irsa_client import SearchOutcome, SiaRecord
from .jobs import Job
from .manifest import sha256_file
from .pipeline import read_spherex_image, reproject_frame
from .service import SearchService, _PreparedFrame, normalize_detector


def import_sequence(entries: list[dict], ra: float, dec: float, fov: float, settings: Settings) -> Job:
    """La URL es una declaración del operador, no autentica el archivo local."""
    ra, dec = validate_ra(ra), validate_dec(dec)
    if not math.isfinite(fov) or not 1 <= fov <= 30:
        raise ValueError("FOV debe ser finito entre 1 y 30 arcmin")
    if not 2 <= len(entries) <= settings.max_frames:
        raise ValueError(f"se requieren 2–{settings.max_frames} recortes; para uno use import_irsa_cutout.py")
    images, records, sources = {}, [], []
    detectors = set()
    total = 0
    for entry in entries:
        path = Path(entry["path"]).resolve()
        source = entry["source_url"]
        parsed = urlsplit(source)
        if (parsed.scheme != "https" or parsed.hostname != "irsa.ipac.caltech.edu"
                or parsed.username or parsed.password or parsed.port not in (None, 443)):
            raise ValueError("se requiere URL HTTPS oficial IRSA sin credenciales")
        release = next((release for release in ("dr1", "qr3")
                        if parsed.path.startswith(f"/ibe/data/spherex/{release}/level2/")), None)
        if release is None:
            raise ValueError("solo recortes Level 2 DR1/QR3, no QR2 ni cubos")
        size = path.stat().st_size
        total += size
        if size > settings.max_download_bytes or total > settings.max_job_download_bytes:
            raise ValueError("archivos locales exceden el presupuesto de bytes del trabajo")
        checksum = sha256_file(path)
        if "sha256" in entry and checksum != entry["sha256"]:
            raise ValueError("SHA-256 local no coincide con el índice de entrada")
        image = read_spherex_image(path, target=(ra, dec))
        detector = normalize_detector(image.detector)
        obs_id = str(image.header.get("OBSID", "")).strip()
        if not detector or not obs_id or not image.version or not image.bunit:
            raise ValueError("recorte sin detector, OBSID, VERSION o BUNIT")
        if obs_id in images:
            raise ValueError("exposición OBSID duplicada; no se cuenta como otra época")
        detectors.add(detector)
        if len(detectors) != 1:
            raise ValueError("una secuencia local debe contener un solo detector")
        header = image.header
        t_min = (float(header["MJD-OBS"]) if "MJD-OBS" in header
                 else float(Time(header["DATE-OBS"], scale="utc").mjd))
        t_max = float(Time(header["DATE-END"], scale="utc").mjd) if "DATE-END" in header else t_min
        if not math.isfinite(t_min) or not math.isfinite(t_max) or t_max < t_min:
            raise ValueError("tiempos FITS no finitos o intervalo inválido")
        images[obs_id] = image
        records.append(SiaRecord(obs_id=obs_id, collection=f"spherex_{release}", access_url=source,
                                 bandpass=detector, t_min=t_min, t_max=t_max, dataproduct_type="image"))
        sources.append({"obs_id": obs_id, "source_url": source, "sha256": checksum})

    class LocalService(SearchService):
        def _find_records(self, job, ra_deg, dec_deg, fov_arcmin):
            return SearchOutcome(records=records, collections=[], warnings=[
                "Importación local sin consulta de red; procedencia declarada por el operador.",
                "No se infiere survey wide/deep de la ruta. No confirma detección ni movimiento.",
            ]), None, False

        def _prepare_frame(self, record, ra_deg, dec_deg, fov_arcmin, target_wcs, shape, budget):
            image = images[record.obs_id]
            if image.valid_fraction < self.settings.min_valid_fraction:
                raise ValueError("cobertura válida de entrada insuficiente")
            processed = reproject_frame(image, target_wcs, shape)
            if processed.valid_fraction < self.settings.min_valid_fraction:
                raise ValueError("cobertura válida de salida insuficiente")
            return _PreparedFrame(record=record, image=image, processed=processed)

    service = LocalService(settings)
    service.search_provenance = {"method": "local-sequence-import",
                                 "sources": sorted(sources, key=lambda item: item["obs_id"]),
                                 "origin_verified": False}
    request = {"ra_deg": ra, "dec_deg": dec, "fov_arcmin": fov,
               "frames": max(settings.min_frames, len(entries)), "detector": next(iter(detectors))}
    job = Job(id="local-sequence", request=request)
    try:
        service.run(job, request)
    finally:
        service.close()
    return job
