"""Ejecuta el pipeline real y registra resultados, incluidos fallos, sin simular datos.

No valida astrometría ni detecciones. Requiere red; no se ejecuta en CI.
Ejemplo: python scripts/verify_real_sequences.py --target all --fov 4
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import PIPELINE_VERSION, Settings  # noqa: E402
from orbitlens.jobs import Job  # noqa: E402
from orbitlens.manifest import read_json, utc_now_iso, validate_result_files, write_json_atomic  # noqa: E402
from orbitlens.service import SearchService  # noqa: E402
from orbitlens.targets import PRESETS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["all", "reference", *(p.id for p in PRESETS)], required=True)
    parser.add_argument("--fov", type=float, default=4.0, help="ancho completo en arcmin")
    parser.add_argument("--detector", choices=["auto", *(f"D{i}" for i in range(1, 7))], default="auto")
    parser.add_argument("--frames", type=int, choices=range(3, 17), default=3)
    parser.add_argument("--maxrec", type=int, default=20)
    parser.add_argument("--max-candidates", type=int, default=6)
    parser.add_argument("--connect-timeout", type=float, default=5)
    parser.add_argument("--read-timeout", type=float, default=12)
    args = parser.parse_args()
    if not 1 <= args.fov <= 30 or args.maxrec < 1 or args.max_candidates < args.frames:
        parser.error("FOV debe ser 1–30; maxrec positivo; max-candidates >= frames")
    settings = replace(Settings.from_env(), search_maxrec=args.maxrec,
                       max_candidates=args.max_candidates, retry_attempts=1,
                       connect_timeout_s=args.connect_timeout, read_timeout_s=args.read_timeout)
    fields = [p.public() for p in PRESETS if args.target in ("all", p.id)]
    if args.target == "reference":
        fields = [{"id": "reference", "ra_deg": 304.693508808, "dec_deg": 42.4436872991,
                   "reference": "Campo del tutorial IRSA Intro, no un objetivo del reto", "verified": False}]
    report = {"started_at": utc_now_iso(), "pipeline_version": PIPELINE_VERSION,
              "code_commit": os.environ.get("ORBITLENS_CODE_COMMIT", "dev"),
              "limits": {**vars(args), "job_timeout_s": settings.job_timeout_s}, "fields": [],
              "limitations": ["Centros aproximados de catálogo propagados a J2026; sin ajuste astrométrico a SPHEREx.",
                              "ready/partial no confirman detección ni movimiento propio.",
                              "Presupuesto temporal cooperativo; no interrumpe un cálculo nativo en curso."]}
    report_path = settings.data_dir / "real-data" / f"sequences-{time.time_ns()}.json"
    service = SearchService(settings)
    try:
        for field in fields:
            request = {"ra_deg": field["ra_deg"], "dec_deg": field["dec_deg"],
                       "fov_arcmin": args.fov, "frames": args.frames, "detector": args.detector}
            if "epoch_jyear" in field:
                request.update(coordinate_epoch_jyear=field["epoch_jyear"], coordinate_reference=field["reference"],
                               coordinate_model=field["coordinate_model"], astrometry_fitted_to_spherex=False)
            job = Job(id=f"verify-{field['id']}", request=request)
            started = time.monotonic()
            print(f"Consultando {field['id']}…", flush=True)
            try:
                service.run(job, request)
                if job.result_id:
                    result_dir = service.results_dir / job.result_id
                    manifest = read_json(result_dir / "manifest.json")
                    validate_result_files(result_dir, manifest)
            except Exception as exc:
                job.update(status="error", phase=None, error=f"{type(exc).__name__}: {exc}")
            entry = {"field": field, "elapsed_s": round(time.monotonic() - started, 3),
                     "job": job.public()}
            report["fields"].append(entry)
            write_json_atomic(report, report_path)
            print(f"{field['id']}: {job.status}; result={job.result_id}; {entry['elapsed_s']} s", flush=True)
    finally:
        service.close()
    report["finished_at"] = utc_now_iso()
    write_json_atomic(report, report_path)
    print(f"Informe: {report_path}", flush=True)
    return 0 if all(entry["job"]["status"] == "ready" for entry in report["fields"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
