"""Descarga UN recorte DR1 del tutorial IRSA y lo publica localmente.

El campo de ejemplo no es ninguno de los cinco presets del reto.
No requiere SIA/TAP ni credenciales; no descarga el FITS completo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import Settings  # noqa: E402
from orbitlens.downloads import download_to_file  # noqa: E402
from scripts.import_irsa_cutout import publish  # noqa: E402

RA, DEC, FOV = 304.693508808, 42.4436872991, 1.2
SOURCE_URL = (
    "https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/"
    "l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits"
    "?center=304.693508808,42.4436872991&size=0.02"
)


def main() -> int:
    settings = Settings.from_env()
    path = settings.data_dir / "real-data" / "tutorial-dr1-cutout.fits"
    if not path.is_file():
        print("Descargando recorte DR1 de referencia (no es un preset del reto)…", flush=True)
        with httpx.Client(timeout=httpx.Timeout(settings.read_timeout_s,
                                               connect=settings.connect_timeout_s)) as client:
            download_to_file(client, SOURCE_URL, path, max_bytes=settings.max_download_bytes,
                             attempts=settings.retry_attempts, backoff=settings.retry_backoff_s,
                             allowed_hosts=settings.allowed_cutout_hosts)
    manifest = publish(path, SOURCE_URL, RA, DEC, FOV, settings)
    print(f"FITS y manifiesto: {manifest.parent}")
    print(f"Abrir: /?result={manifest.parent.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
