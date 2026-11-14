"""Contrasta los campos reales previos con predicciones de catálogo sin detectar fuentes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.astrometry import SNAPSHOT, position_at  # noqa: E402
from orbitlens.config import Settings  # noqa: E402
from orbitlens.manifest import read_json, utc_now_iso, write_json_atomic  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/real-data/astrometry-audit.json"))
    args = parser.parse_args()
    report = read_json(args.acquisition_report)
    fields = []
    for item in report["fields"]:
        target = item["field"]["id"]
        result_id = item["job"].get("result_id")
        if not result_id:
            continue
        root = Settings.from_env().data_dir / "results" / result_id
        manifest = read_json(root / "manifest.json")
        checked = []
        for frame in manifest["frames"]:
            epoch = float(Time(frame["time"]["t_min_mjd"], format="mjd", scale="utc").jyear)
            ra, dec = position_at(target, epoch)
            request = manifest["request"]
            separation = SkyCoord(ra, dec, unit="deg").separation(SkyCoord(request["ra_deg"], request["dec_deg"], unit="deg")).arcsec
            with fits.open(root / frame["fits"]) as hdul:
                wcs = WCS(hdul[0].header).celestial
                data = hdul[0].data
                x, y = wcs.world_to_pixel_values(ra, dec)
                inside = bool(np.isfinite(x) and np.isfinite(y) and -0.5 <= x < data.shape[1] - 0.5 and -0.5 <= y < data.shape[0] - 0.5)
                valid = bool(np.isfinite(data[int(np.floor(y + 0.5)), int(np.floor(x + 0.5))])) if inside else False
            checked.append({"obs_id": frame["obs_id"], "epoch_jyear": epoch, "predicted_ra_deg": ra,
                            "predicted_dec_deg": dec, "separation_from_requested_center_arcsec": float(separation),
                            "inside_output": inside, "nearest_output_pixel_valid": valid})
        fields.append({"target": target, "result_id": result_id, "catalog": SNAPSHOT["entries"][target],
                       "frames": checked, "recommended_center_J2026": position_at(target, 2026.0)})
    write_json_atomic({"created_at": utc_now_iso(), "source": SNAPSHOT,
                       "limitations": "Predicción tangencial: sin paralaje anual, RV, aceleración ni movimiento orbital. No detección ni ajuste astrométrico a SPHEREx.",
                       "fields": fields}, args.output)
    print(f"Auditoría: {args.output}")
    for field in fields:
        print(field["target"], field["recommended_center_J2026"],
              "dentro de salida:", [f["inside_output"] for f in field["frames"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
