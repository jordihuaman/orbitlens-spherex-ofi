"""Manifiestos reproducibles de resultados y utilidades de archivos."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = [
    "REQUIRED_TOP_LEVEL",
    "utc_now_iso",
    "sha256_file",
    "write_json_atomic",
    "read_json",
    "validate_manifest",
]

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "pipeline_version",
    "code_commit",
    "result_id",
    "created_at",
    "request",
    "search",
    "grid",
    "processing",
    "frames",
    "warnings",
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(data: dict[str, Any], path: Path) -> None:
    """Escribe JSON de forma atómica para no publicar manifiestos a medias."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Valida la estructura mínima antes de publicar un resultado."""

    missing = [key for key in REQUIRED_TOP_LEVEL if key not in manifest]
    if missing:
        raise ValueError(f"manifiesto incompleto; faltan: {', '.join(missing)}")

    frames = manifest.get("frames")
    if not isinstance(frames, list):
        raise ValueError("manifest['frames'] debe ser una lista")
    for index, frame in enumerate(frames):
        for key in ("frame_id", "png", "fits", "time"):
            if key not in frame:
                raise ValueError(f"frame {index} sin campo obligatorio {key!r}")
