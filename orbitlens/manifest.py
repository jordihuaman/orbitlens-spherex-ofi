"""Manifiestos reproducibles de resultados y utilidades de archivos."""

from __future__ import annotations

import hashlib
import json
import os
import re
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
    "validate_file_entry",
    "validate_result_files",
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
        if not isinstance(frame, dict):
            raise ValueError(f"frame {index} debe ser un objeto")
        for key in ("frame_id", "png", "fits", "time"):
            if key not in frame:
                raise ValueError(f"frame {index} sin campo obligatorio {key!r}")
    # Rechazar NaN/Infinity incluso en metadatos anidados.
    json.dumps(manifest, allow_nan=False)


def validate_file_entry(result_dir: Path, entry: dict[str, Any]) -> Path:
    """Comprueba contención, tamaño y SHA-256 antes de reutilizar o servir."""
    if not isinstance(entry, dict) or entry.get("kind") not in {"png", "fits"}:
        raise ValueError("entrada de archivo inválida")
    relative = entry.get("path")
    if not isinstance(relative, str) or not relative:
        raise ValueError("archivo sin ruta")
    root = Path(result_dir).resolve()
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root) or not path.is_file():
        raise ValueError("archivo ausente o fuera del resultado")
    size, checksum = entry.get("bytes"), entry.get("sha256")
    if type(size) is not int or size <= 0 or path.stat().st_size != size:
        raise ValueError("tamaño de archivo incorrecto")
    if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
        raise ValueError("SHA-256 inválido")
    if sha256_file(path) != checksum:
        raise ValueError("SHA-256 no coincide: archivo corrupto")
    return path


def validate_result_files(result_dir: Path, manifest: dict[str, Any]) -> None:
    validate_manifest(manifest)
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("resultado sin índice de archivos")
    ids: set[str] = set()
    paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("entrada sin ID de archivo")
        validate_file_entry(result_dir, entry)
        if entry["id"] in ids or entry.get("path") in paths:
            raise ValueError("ID o ruta de archivo duplicado")
        ids.add(entry["id"])
        paths.add(entry["path"])
    for frame in manifest["frames"]:
        for field in ("png", "fits", "original_fits"):
            if field in frame and frame[field] not in paths:
                raise ValueError(f"frame referencia {field} sin indexar")
