"""Caché de archivos en disco, con claves estables y escritura atómica."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

__all__ = ["FileCache"]


def _key(*parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FileCache:
    """Caché simple por namespace; no comparte estado entre procesos."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def key(self, *parts: object) -> str:
        return _key(*parts)

    def path(self, namespace: str, key: str, filename: str) -> Path:
        safe_name = Path(filename).name
        return self.root / namespace / key / safe_name

    def exists(self, namespace: str, key: str, filename: str) -> bool:
        return self.path(namespace, key, filename).is_file()

    def write_bytes(self, namespace: str, key: str, filename: str, content: bytes) -> Path:
        destination = self.path(namespace, key, filename)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + f".{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination

    def write_json(self, namespace: str, key: str, filename: str, data: Any) -> Path:
        text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        return self.write_bytes(namespace, key, filename, text.encode("utf-8"))

    def read_json(self, namespace: str, key: str, filename: str) -> Any:
        path = self.path(namespace, key, filename)
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        os.utime(path, (time.time(), path.stat().st_mtime))
        return data

    def is_fresh(self, namespace: str, key: str, filename: str, ttl_hours: float) -> bool:
        path = self.path(namespace, key, filename)
        if not path.is_file():
            return False
        age_hours = (time.time() - path.stat().st_mtime) / 3600.0
        return age_hours <= ttl_hours

    def directory_size(self) -> int:
        total = 0
        for path in self.root.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total

    def clear(self) -> None:
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
