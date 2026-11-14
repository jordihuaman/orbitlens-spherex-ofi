"""Indexa resultados reales íntegros y centrados según los presets vigentes.

No modifica FITS, no cambia verified y no indexa paquetes sintéticos.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import Settings  # noqa: E402
from orbitlens.manifest import read_json, validate_result_files, write_json_atomic  # noqa: E402
from orbitlens.targets import get_preset  # noqa: E402


def build_index(report: dict, data_dir: Path) -> dict[str, str]:
    index = {}
    for item in report["fields"]:
        preset = get_preset(item["field"]["id"])
        result_id = item["job"].get("result_id")
        if preset is None or not isinstance(result_id, str) or not re.fullmatch(r"[a-f0-9]{16}", result_id):
            continue
        root = data_dir / "results" / result_id
        manifest = read_json(root / "manifest.json")
        validate_result_files(root, manifest)
        if manifest["result_id"] != result_id:
            raise ValueError("ID del manifiesto no coincide con su directorio")
        if any(frame["collection"] == "synthetic-demo" for frame in manifest["frames"]):
            raise ValueError("no se indexan presets sintéticos")
        for key in ("ra_deg", "dec_deg"):
            if abs(manifest["request"][key] - getattr(preset, key)) > 1e-7:
                raise ValueError(f"el resultado de {preset.id} usa un centro anterior; regenerar")
        index[preset.id] = result_id
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    settings = Settings.from_env()
    index = build_index(read_json(args.report), settings.data_dir)
    # Actualizar entradas presentes sin eliminar índices anteriores por fallos de red.
    path = settings.data_dir / "presets.json"
    existing = read_json(path) if path.is_file() else {}
    if not isinstance(existing, dict):
        raise ValueError("índice existente inválido; reparar sin sobrescribirlo silenciosamente")
    write_json_atomic({**existing, **index}, path)
    print(f"Indexados {len(index)} presets reales: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
