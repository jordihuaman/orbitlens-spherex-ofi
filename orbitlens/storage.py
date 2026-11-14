"""Presupuesto blando de disco con LRU conservador de caché regenerable.

Los resultados publicados y las entradas del operador nunca se borran aquí.
Durante actividad no se expulsa caché: pueden estar leyéndola otros trabajos.
"""

from __future__ import annotations

import re
import shutil
import threading
from contextlib import contextmanager
from pathlib import Path

from .execution import DeadlineExceeded, remaining_seconds


class StorageError(RuntimeError):
    pass


class StorageManager:
    def __init__(self, root: Path, max_bytes: int, min_free_bytes: int):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.min_free_bytes = min_free_bytes
        self._active = 0
        self._lock = threading.RLock()

    def usage(self) -> int:
        total = 0
        for path in self.root.rglob("*"):
            try:
                if path.is_file() and not path.is_symlink():
                    total += path.stat().st_size
            except FileNotFoundError:
                # Un temporal puede haberse publicado/renombrado entre ambas lecturas.
                continue
        return total

    def maintain(self) -> dict:
        with self._lock:
            used = self.usage()
            removed = 0
            if not self._active and not (self.root / "cache").is_symlink():
                entries = []
                for namespace in ("sia", "cutout"):
                    directory = self.root / "cache" / namespace
                    if directory.is_symlink():
                        continue
                    for entry in directory.glob("*"):
                        if not re.fullmatch(r"[a-f0-9]{64}", entry.name) or entry.is_symlink() or not entry.is_dir():
                            continue
                        files = list(entry.rglob("*"))
                        if any(path.is_symlink() for path in files):
                            continue
                        size = sum(path.stat().st_size for path in files if path.is_file())
                        accessed = max((path.stat().st_atime for path in files if path.is_file()), default=0)
                        entries.append((accessed, entry, size))
                for _, entry, size in sorted(entries):
                    if used <= self.max_bytes and shutil.disk_usage(self.root).free >= self.min_free_bytes:
                        break
                    # Solo una entrada de caché generada, inactiva y contenida.
                    if not entry.resolve().is_relative_to(self.root):
                        continue
                    shutil.rmtree(entry)
                    removed += 1
                    used -= size
            return {"bytes": used, "max_bytes": self.max_bytes, "removed_cache_entries": removed,
                    "active_builders": self._active, "results_policy": "protected"}

    def ensure_space(self, additional: int = 0) -> None:
        with self._lock:
            if self.usage() + additional > self.max_bytes:
                raise StorageError("presupuesto de disco agotado; resultados protegidos, libere espacio o amplíe el límite")
            if shutil.disk_usage(self.root).free < self.min_free_bytes + additional:
                raise StorageError("espacio libre insuficiente; descarga detenida sin borrar resultados")

    @contextmanager
    def activity(self):
        with self._lock:
            self.maintain()
            self.ensure_space()
            self._active += 1
        try:
            yield
        finally:
            with self._lock:
                self._active -= 1


class KeyedLocks:
    def __init__(self):
        self._guard = threading.Lock()
        self._entries = {}

    @contextmanager
    def hold(self, key):
        with self._guard:
            lock, count = self._entries.get(key, (threading.Lock(), 0))
            self._entries[key] = (lock, count + 1)
        try:
            remaining = remaining_seconds()
            acquired = lock.acquire(timeout=remaining) if remaining is not None else lock.acquire()
            if not acquired:
                raise DeadlineExceeded("presupuesto agotado esperando publicación/caché")
            try:
                yield
            finally:
                lock.release()
        finally:
            with self._guard:
                _, count = self._entries[key]
                if count == 1:
                    del self._entries[key]
                else:
                    self._entries[key] = (lock, count - 1)
