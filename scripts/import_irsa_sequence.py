"""Importa varios recortes IRSA locales y publica una secuencia sin consultar red.

Índice JSON: {"ra_deg":10,"dec_deg":20,"fov_arcmin":4,"files":[
  {"path":"cutout.fits","source_url":"https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/…"}
]}. Las rutas son relativas al índice. sha256 es opcional para comprobar entrada.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import Settings  # noqa: E402
from orbitlens.local_sequence import import_sequence  # noqa: E402
from orbitlens.manifest import read_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    args = parser.parse_args()
    index = read_json(args.index)
    entries = [{**entry, "path": args.index.resolve().parent / entry["path"]} for entry in index["files"]]
    job = import_sequence(entries, index["ra_deg"], index["dec_deg"], index["fov_arcmin"], Settings.from_env())
    print(job.public())
    if job.result_id:
        print(f"Abrir: /?result={job.result_id}")
    return 0 if job.status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
