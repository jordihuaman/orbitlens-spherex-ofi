"""Genera un resultado SINTÉTICO para probar la UI sin depender de IRSA.

No son datos de SPHEREx. El manifiesto lo declara y la interfaz muestra los
avisos. Sirve para verificar el contrato API → manifiesto → PNG/FITS → visor.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\make_demo_result.py
"""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import PIPELINE_VERSION, SCHEMA_VERSION, Settings  # noqa: E402
from orbitlens.manifest import (  # noqa: E402
    sha256_file,
    utc_now_iso,
    validate_manifest,
    write_json_atomic,
)
from orbitlens.masks import FlagDefinitions  # noqa: E402
from orbitlens.pipeline import (  # noqa: E402
    ProcessedFrame,
    SpherexImage,
    build_target_wcs,
    compute_stretch_limits,
    render_rgba,
    write_derived_fits,
    write_png,
)
from orbitlens.service import mjd_to_iso, sanitize_name  # noqa: E402

FRAMES = 8


def _dummy_image(wcs: WCS, shape: tuple[int, int]) -> SpherexImage:
    return SpherexImage(
        path=Path("synthetic.fits"),
        data=np.zeros(shape),
        flags=None,
        header=fits.Header(),
        wcs=wcs,
        flag_definitions=FlagDefinitions(bits={}, source="none"),
        valid=np.ones(shape, dtype=bool),
        valid_fraction=1.0,
        center_valid=True,
        lambda_um=1.6,
        bandwidth_um=0.1,
        detector="DEMO",
        version="synthetic",
        bunit="MJy/sr",
        warnings=("Frame sintético de demostración.",),
    )


def main() -> int:
    settings = Settings(data_dir=Path("data"))
    result_id = hashlib.sha256(b"orbitlens-synthetic-demo-v1").hexdigest()[:16]
    result_dir = settings.data_dir / "results" / result_id
    frames_dir = result_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    ra_deg, dec_deg, fov = 269.45208, 4.69339, 10.0
    target_wcs, width, height = build_target_wcs(
        ra_deg, dec_deg, fov, pixel_scale_arcsec=settings.pixel_scale_arcsec
    )
    shape = (height, width)
    yy, xx = np.mgrid[0:height, 0:width]

    frames: list[ProcessedFrame] = []
    for index in range(FRAMES):
        cx = width / 2 + index * 1.2 - 4
        cy = height / 2 + math.sin(index / 2) * 2
        source = 8.0 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 2.5**2))
        noise = np.random.default_rng(1000 + index).normal(0.0, 0.25, shape)
        data = 1.0 + source + noise
        frames.append(
            ProcessedFrame(
                source=_dummy_image(target_wcs, shape),
                data=data,
                valid=np.ones(shape, dtype=bool),
            )
        )

    vmin, vmax = compute_stretch_limits(frames)
    frame_entries: list[dict[str, object]] = []
    file_entries: list[dict[str, object]] = []

    for index, frame in enumerate(frames, start=1):
        frame_id = f"{index:02d}_demo"
        png_rel = f"frames/{frame_id}.png"
        fits_rel = f"frames/{frame_id}.fits"
        png_path = result_dir / png_rel
        fits_path = result_dir / fits_rel
        write_png(render_rgba(frame, vmin, vmax), png_path)
        write_derived_fits(
            frame.data,
            target_wcs,
            fits_path,
            metadata={"OBSID": f"DEMO-{index:02d}", "BUNIT": "MJy/sr"},
        )
        t_min = 61000.0 + (index - 1) * 12.0
        frame_entries.append(
            {
                "frame_id": frame_id,
                "png": png_rel,
                "fits": fits_rel,
                "obs_id": f"DEMO-{index:02d}",
                "collection": "synthetic-demo",
                "detector": "DEMO",
                "version": "synthetic",
                "time": {
                    "t_min_mjd": t_min,
                    "t_max_mjd": t_min + 0.1,
                    "label": mjd_to_iso(t_min),
                },
                "lambda_um": 1.6,
                "bandwidth_um": 0.1,
                "valid_fraction": 1.0,
                "center_valid": True,
                "warnings": ["Frame sintético de demostración."],
            }
        )
        for kind, relative, path in (
            ("png", png_rel, png_path),
            ("fits", fits_rel, fits_path),
        ):
            file_entries.append(
                {
                    "id": f"{sanitize_name(frame_id)}-{kind}",
                    "kind": kind,
                    "path": relative,
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "code_commit": "synthetic-demo",
        "result_id": result_id,
        "created_at": utc_now_iso(),
        "request": {
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "fov_arcmin": fov,
            "frames": FRAMES,
            "detector": "auto",
            "target_name": "barnard",
        },
        "search": {
            "queried_at": utc_now_iso(),
            "collections": ["synthetic-demo"],
            "records_found": FRAMES,
            "candidates": FRAMES,
            "selected": FRAMES,
            "overflow": False,
            "from_cache": False,
            "selection": "demostración sintética",
        },
        "grid": {
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "fov_arcmin": fov,
            "width": width,
            "height": height,
            "pixel_scale_arcsec": settings.pixel_scale_arcsec,
            "projection": "RA---TAN/DEC--TAN, norte arriba",
        },
        "processing": {
            "mask_policy_version": "demo",
            "min_valid_fraction": 0.0,
            "background": "sintético",
            "stretch": {"mode": "asinh", "vmin": vmin, "vmax": vmax, "softening": 0.05},
            "spectral_policy": "demostración; no usar para ciencia",
        },
        "frames": frame_entries,
        "files": file_entries,
        "warnings": [
            "RESULTADO SINTÉTICO: no son imágenes de SPHEREx ni una detección.",
            "Sirve solo para probar el reproductor y el contrato de archivos.",
        ],
    }
    validate_manifest(manifest)
    write_json_atomic(manifest, result_dir / "manifest.json")
    print(f"Resultado sintético: {result_id}")
    print(f"Abrir: /?result={result_id}")
    print(f"Manifiesto: /api/results/{result_id}/manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
