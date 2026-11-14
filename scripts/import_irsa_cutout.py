"""Publica un recorte IRSA local con original, derivado, PNG y manifiesto.

No consulta SIA ni inventa observaciones: usa tiempos/OBSID del propio FITS.
Útil para descargas manuales del Data Explorer o referencias oficiales.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from astropy.io import fits
from astropy.time import Time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import PIPELINE_VERSION, SCHEMA_VERSION, Settings  # noqa: E402
from orbitlens.coordinates import validate_dec, validate_ra  # noqa: E402
from orbitlens.manifest import sha256_file, utc_now_iso, validate_manifest, write_json_atomic  # noqa: E402
from orbitlens.pipeline import (  # noqa: E402
    build_target_wcs,
    compute_stretch_limits,
    read_spherex_image,
    render_rgba,
    reproject_frame,
    write_derived_fits,
    write_png,
)
from orbitlens.service import mjd_to_iso, normalize_detector  # noqa: E402


def publish(path: Path, source_url: str, ra: float, dec: float, fov: float,
            settings: Settings) -> Path:
    ra, dec = validate_ra(ra), validate_dec(dec)
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.hostname != "irsa.ipac.caltech.edu":
        raise ValueError("source-url debe ser una URL HTTPS de IRSA")
    release = next((value for value in ("dr1", "qr3")
                    if parsed.path.startswith(f"/ibe/data/spherex/{value}/level2/")), None)
    if release is None:
        raise ValueError("se requiere un recorte de imagen Level 2 DR1/QR3, no QR2 ni un cubo")
    image = read_spherex_image(path, target=(ra, dec))
    detector = normalize_detector(image.detector)
    if detector is None:
        raise ValueError("el FITS no identifica un detector SPHEREx 1–6")
    header = image.header
    obs_id = str(header.get("OBSID", "")).strip()
    if not obs_id or not image.version or not image.bunit:
        raise ValueError("faltan OBSID, VERSION o BUNIT; no se publicará una procedencia incompleta")
    t_min = float(header["MJD-OBS"]) if "MJD-OBS" in header else float(Time(header["DATE-OBS"], scale="utc").mjd)
    t_max = float(Time(header["DATE-END"], scale="utc").mjd) if "DATE-END" in header else t_min
    if t_max < t_min:
        raise ValueError("intervalo de observación inválido")
    wcs, width, height = build_target_wcs(ra, dec, fov, pixel_scale_arcsec=settings.pixel_scale_arcsec)
    processed = reproject_frame(image, wcs, (height, width))
    vmin, vmax = compute_stretch_limits([processed])
    original_sha = sha256_file(path)
    identity = [original_sha, source_url, ra, dec, fov, settings.pixel_scale_arcsec, PIPELINE_VERSION]
    result_id = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:16]
    output = settings.data_dir / "results" / result_id
    output.mkdir(parents=True, exist_ok=True)
    original = output / "original.fits"
    if path.resolve() != original.resolve():
        shutil.copyfile(path, original)
    derived = output / "aligned.fits"
    png = output / "preview.png"
    write_derived_fits(processed.data, wcs, derived, metadata={
        "OBSID": obs_id, "COLLECT": f"spherex_{release}", "BUNIT": image.bunit,
        "VERSION": image.version, "DETECTOR": detector,
    })
    write_png(render_rgba(processed, vmin, vmax), png)
    with fits.open(original, memmap=False) as hdul:
        hdus = [{"name": hdu.name, "type": type(hdu).__name__,
                 "shape": list(hdu.data.shape) if hdu.data is not None else None} for hdu in hdul]
    warnings = [*image.warnings,
                "Recorte real aislado: no constituye una secuencia temporal ni una detección confirmada.",
                "Importación local; la URL de procedencia fue proporcionada por el operador, sin consulta SIA."]
    manifest = {
        "schema_version": SCHEMA_VERSION, "pipeline_version": PIPELINE_VERSION,
        "code_commit": os.environ.get("ORBITLENS_CODE_COMMIT", "dev"),
        "result_id": result_id, "created_at": utc_now_iso(),
        "request": {"ra_deg": ra, "dec_deg": dec, "fov_arcmin": fov,
                    "frames": 1, "detector": detector},
        "search": {"method": "local-import", "release": release, "source_url": source_url,
                   "queried_at": None, "records_found": 1, "selected": 1,
                   "detector_selected": detector,
                   "survey": "no inferido; no se distingue wide/deep por la ruta del archivo"},
        "grid": {"ra_deg": ra, "dec_deg": dec, "fov_arcmin": fov,
                 "width": width, "height": height, "pixel_scale_arcsec": settings.pixel_scale_arcsec,
                 "projection": "RA---TAN/DEC--TAN"},
        "processing": {"mask_policy_version": "1.0", "spectral_location": "coordenada solicitada",
                       "stretch": {"mode": "asinh", "vmin": vmin, "vmax": vmax}},
        "frames": [{"frame_id": "01_real", "png": png.name, "fits": derived.name,
                    "original_fits": original.name, "obs_id": obs_id,
                    "collection": f"spherex_{release} (survey no inferido)",
                    "detector": detector, "version": image.version, "bunit": image.bunit,
                    "time": {"t_min_mjd": t_min, "t_max_mjd": t_max, "label": mjd_to_iso(t_min)},
                    "lambda_um": image.lambda_um, "bandwidth_um": image.bandwidth_um,
                    "valid_fraction": processed.valid_fraction, "center_valid": processed.center_valid,
                    "warnings": list(image.warnings)}],
        "inspection": {"hdus": hdus, "input_valid_fraction": image.valid_fraction,
                       "flags": image.flag_definitions.bits,
                       "source_url": source_url, "original_sha256": original_sha},
        "files": [{"id": file_id, "kind": kind, "path": file.name,
                   "sha256": sha256_file(file), "bytes": file.stat().st_size}
                  for file_id, kind, file in [("01_real-original", "fits", original),
                                              ("01_real-fits", "fits", derived),
                                              ("01_real-png", "png", png)]],
        "warnings": warnings,
    }
    validate_manifest(manifest)
    write_json_atomic(manifest, output / "manifest.json")
    return output / "manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fits", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--ra", type=float, required=True)
    parser.add_argument("--dec", type=float, required=True)
    parser.add_argument("--fov", type=float, required=True, help="ancho en arcmin")
    args = parser.parse_args()
    manifest = publish(args.fits, args.source_url, args.ra, args.dec, args.fov, Settings.from_env())
    print(f"Manifiesto: {manifest}")
    print(f"Abrir: /?result={manifest.parent.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
