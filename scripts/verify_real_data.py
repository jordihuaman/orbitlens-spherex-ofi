"""Verificación acotada contra IRSA: una coordenada → un cutout → PNG.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\verify_real_data.py --target barnard
    .\\.venv\\Scripts\\python.exe scripts\\verify_real_data.py --target wise0855 --download

No forma parte de la suite automática: requiere red y datos reales. Registra
fallos en lugar de simular éxito.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import DEFAULT_COLLECTIONS, PIPELINE_VERSION, SCHEMA_VERSION, Settings  # noqa: E402
from orbitlens.downloads import download_to_file  # noqa: E402
from orbitlens.irsa_client import search  # noqa: E402
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
from orbitlens.service import mjd_to_iso, normalize_detector, select_detector  # noqa: E402
from orbitlens.targets import get_preset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="barnard")
    parser.add_argument("--fov", type=float, default=10.0)
    parser.add_argument("--maxrec", type=int, default=5)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--detector", choices=["auto", "D1", "D2", "D3", "D4", "D5", "D6"], default="auto")
    args = parser.parse_args()

    preset = get_preset(args.target)
    if preset is None:
        print(f"Objetivo desconocido: {args.target}")
        return 2

    settings = Settings.from_env()
    timeout = httpx.Timeout(settings.read_timeout_s, connect=settings.connect_timeout_s)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        print(
            f"Consulta SIA: {preset.name} RA={preset.ra_deg:.6f} "
            f"Dec={preset.dec_deg:.6f} FOV={args.fov}′"
        )
        outcome = search(
            client,
            settings,
            preset.ra_deg,
            preset.dec_deg,
            args.fov,
            maxrec=args.maxrec,
        )
        print(f"Colecciones: {outcome.collections}")
        print(f"Registros: {len(outcome.records)}  overflow={outcome.overflow}")
        for warning in outcome.warnings:
            print(f"AVISO: {warning}")
        for record in outcome.records[:10]:
            print(
                f"- {record.collection} {record.obs_id} "
                f"band={record.bandpass} t_min={record.t_min} "
                f"url={record.access_url[:90]}"
            )

        if not outcome.records:
            print("No se descargó nada: la consulta no devolvió imágenes.")
            return 1

        if not args.download:
            return 0

        eligible = [record for record in outcome.records
                    if record.collection in DEFAULT_COLLECTIONS and record.t_min is not None
                    and record.dataproduct_type in (None, "image")]
        records, detector = select_detector(eligible, args.detector)
        if not records:
            print("Sin imágenes DR1/QR3 fechadas del detector solicitado; no se cambia de detector.")
            return 1
        record = sorted(records, key=lambda item: item.sort_key)[0]
        size_deg = min(5.0, args.fov / 60.0 * settings.cutout_margin)
        url = record.cutout_url(
            preset.ra_deg,
            preset.dec_deg,
            size_deg,
            allowed_hosts=settings.allowed_cutout_hosts,
        )
        result_id = hashlib.sha256(
            f"verify:{PIPELINE_VERSION}:{record.collection}:{record.obs_id}:{preset.ra_deg}:{preset.dec_deg}:{args.fov}".encode()
        ).hexdigest()[:16]
        raw_dir = settings.data_dir / "results" / result_id
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / "cutout.fits"
        print(f"Descargando {url}")
        download_to_file(client, url, raw_path, max_bytes=settings.max_download_bytes,
                          attempts=settings.retry_attempts, backoff=settings.retry_backoff_s,
                          allowed_hosts=settings.allowed_cutout_hosts)
        print(f"FITS: {raw_path} ({raw_path.stat().st_size} bytes)")

        image = read_spherex_image(raw_path, target=(preset.ra_deg, preset.dec_deg))
        actual = normalize_detector(image.detector)
        if actual is not None and actual != detector:
            raise ValueError("El detector del FITS contradice los metadatos SIA")
        print(
            f"IMAGE {image.data.shape} detector={image.detector} "
            f"version={image.version} bunit={image.bunit}"
        )
        print(
            f"cobertura válida={image.valid_fraction:.1%} "
            f"centro={'válido' if image.center_valid else 'enmascarado'} "
            f"λ={image.lambda_um} µm ancho={image.bandwidth_um} µm"
        )
        for warning in image.warnings:
            print(f"AVISO FITS: {warning}")

        target_wcs, width, height = build_target_wcs(
            preset.ra_deg,
            preset.dec_deg,
            args.fov,
            pixel_scale_arcsec=settings.pixel_scale_arcsec,
        )
        processed = reproject_frame(image, target_wcs, (height, width))
        vmin, vmax = compute_stretch_limits([processed])
        png_path = raw_dir / "preview.png"
        write_png(render_rgba(processed, vmin, vmax), png_path)
        derived_path = raw_dir / "aligned.fits"
        write_derived_fits(processed.data, target_wcs, derived_path,
                           metadata={"OBSID": record.obs_id, "COLLECT": record.collection,
                                     "BUNIT": image.bunit})
        files = [{"id": file_id, "kind": kind, "path": path.name,
                  "sha256": sha256_file(path), "bytes": path.stat().st_size}
                 for file_id, kind, path in [("01_real-png", "png", png_path),
                                             ("01_real-fits", "fits", derived_path),
                                             ("01_real-original", "fits", raw_path)]]
        manifest = {
            "schema_version": SCHEMA_VERSION, "pipeline_version": PIPELINE_VERSION,
            "code_commit": os.environ.get("ORBITLENS_CODE_COMMIT", "dev"),
            "result_id": result_id, "created_at": utc_now_iso(),
            "request": {"target_name": preset.id, "ra_deg": preset.ra_deg,
                        "dec_deg": preset.dec_deg, "fov_arcmin": args.fov,
                        "detector": args.detector, "coordinate_reference": preset.reference,
                        "verified": preset.verified},
            "search": {"collections": outcome.collections, "queried_at": utc_now_iso(),
                       "overflow": outcome.overflow, "detector_selected": detector,
                       "records_found": len(outcome.records), "maxrec": args.maxrec},
            "grid": {"ra_deg": preset.ra_deg, "dec_deg": preset.dec_deg,
                     "fov_arcmin": args.fov, "width": width, "height": height,
                     "pixel_scale_arcsec": settings.pixel_scale_arcsec,
                     "projection": "RA---TAN/DEC--TAN"},
            "processing": {"purpose": "verificación de un recorte real; no secuencia temporal",
                           "stretch": {"vmin": vmin, "vmax": vmax}},
            "frames": [{"frame_id": "01_real", "png": png_path.name,
                        "fits": derived_path.name, "original_fits": raw_path.name,
                        "obs_id": record.obs_id, "collection": record.collection,
                        "access_url": record.access_url, "cutout_url": url,
                        "detector": detector, "version": image.version, "bunit": image.bunit,
                        "time": {"t_min_mjd": record.t_min, "t_max_mjd": record.t_max,
                                 "label": mjd_to_iso(record.t_min)},
                        "lambda_um": image.lambda_um, "bandwidth_um": image.bandwidth_um,
                        "valid_fraction": processed.valid_fraction,
                        "center_valid": processed.center_valid, "warnings": list(image.warnings)}],
            "files": files,
            "warnings": [*outcome.warnings, "Un recorte real no demuestra detección ni movimiento."],
        }
        validate_manifest(manifest)
        write_json_atomic(manifest, raw_dir / "manifest.json")
        print(f"Manifiesto: {raw_dir / 'manifest.json'}; abrir /?result={result_id}")
        print(
            f"PNG: {png_path} rejilla={width}x{height} "
            f"vmin={vmin:.4g} vmax={vmax:.4g} "
            f"cobertura={processed.valid_fraction:.1%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
