"""Verificación acotada contra IRSA: una coordenada → un cutout → PNG.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\verify_real_data.py --target barnard
    .\\.venv\\Scripts\\python.exe scripts\\verify_real_data.py --target wise0855 --download

No forma parte de la suite automática: requiere red y datos reales. Registra
fallos en lugar de simular éxito.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import Settings  # noqa: E402
from orbitlens.irsa_client import search  # noqa: E402
from orbitlens.pipeline import (  # noqa: E402
    build_target_wcs,
    compute_stretch_limits,
    read_spherex_image,
    render_rgba,
    reproject_frame,
    write_png,
)
from orbitlens.targets import get_preset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="barnard")
    parser.add_argument("--fov", type=float, default=10.0)
    parser.add_argument("--maxrec", type=int, default=5)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    preset = get_preset(args.target)
    if preset is None:
        print(f"Objetivo desconocido: {args.target}")
        return 2

    settings = Settings(data_dir=Path("data"))
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

        record = outcome.records[0]
        size_deg = min(5.0, args.fov / 60.0 * settings.cutout_margin)
        url = record.cutout_url(
            preset.ra_deg,
            preset.dec_deg,
            size_deg,
            allowed_hosts=settings.allowed_cutout_hosts,
        )
        raw_dir = settings.data_dir / "verify"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / "cutout.fits"
        print(f"Descargando {url}")
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with raw_path.open("wb") as handle:
                for chunk in response.iter_bytes(1024 * 1024):
                    handle.write(chunk)
        print(f"FITS: {raw_path} ({raw_path.stat().st_size} bytes)")

        image = read_spherex_image(raw_path)
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
        print(
            f"PNG: {png_path} rejilla={width}x{height} "
            f"vmin={vmin:.4g} vmax={vmax:.4g} "
            f"cobertura={processed.valid_fraction:.1%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
