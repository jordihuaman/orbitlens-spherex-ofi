from __future__ import annotations

import math

import pytest

from orbitlens.manifest import (
    REQUIRED_TOP_LEVEL,
    read_json,
    sha256_file,
    utc_now_iso,
    validate_manifest,
    write_json_atomic,
)


def _valid_manifest() -> dict:
    manifest = {key: None for key in REQUIRED_TOP_LEVEL}
    manifest.update(
        {
            "schema_version": 1,
            "pipeline_version": "0.1.0",
            "code_commit": "test",
            "result_id": "a" * 16,
            "created_at": utc_now_iso(),
            "request": {},
            "search": {},
            "grid": {},
            "processing": {},
            "frames": [
                {"frame_id": "01_x", "png": "frames/x.png", "fits": "frames/x.fits", "time": {}}
            ],
            "warnings": [],
        }
    )
    return manifest


def test_valid_manifest_passes() -> None:
    validate_manifest(_valid_manifest())


def test_missing_key_fails() -> None:
    manifest = _valid_manifest()
    del manifest["grid"]
    with pytest.raises(ValueError, match="grid"):
        validate_manifest(manifest)


def test_frame_without_required_field_fails() -> None:
    manifest = _valid_manifest()
    del manifest["frames"][0]["time"]
    with pytest.raises(ValueError, match="time"):
        validate_manifest(manifest)


def test_write_json_is_atomic_and_rejects_nan(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    write_json_atomic({"ok": 1}, path)
    assert read_json(path) == {"ok": 1}
    assert not list(tmp_path.glob("*.tmp"))

    with pytest.raises(ValueError):
        write_json_atomic({"bad": math.nan}, path)


def test_sha256_file(tmp_path) -> None:
    import hashlib

    path = tmp_path / "data.bin"
    path.write_bytes(b"orbitlens")
    assert sha256_file(path) == hashlib.sha256(b"orbitlens").hexdigest()
