import os

import pytest

from orbitlens.storage import KeyedLocks, StorageError, StorageManager


def test_lru_evicts_only_generated_cache_never_results_or_manual_data(tmp_path):
    old = tmp_path / "cache" / "cutout" / ("a" * 64) / "old.fits"
    new = tmp_path / "cache" / "cutout" / ("b" * 64) / "new.fits"
    result = tmp_path / "results" / "keep" / "original.fits"
    for path in (old, new, result):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * 10)
    os.utime(old, (10, 10))
    os.utime(new, (20, 20))
    storage = StorageManager(tmp_path, 20, 0)
    report = storage.maintain()
    assert report["removed_cache_entries"] == 1
    assert not old.exists()
    assert new.exists() and result.exists()


def test_active_cache_is_protected_and_budget_failure_is_recoverable(tmp_path):
    file = tmp_path / "cache" / "sia" / ("a" * 64) / "search.json"
    file.parent.mkdir(parents=True)
    file.write_bytes(b"x")
    storage = StorageManager(tmp_path, 2, 0)
    with storage.activity():
        file.write_bytes(b"xxx")
        assert storage.maintain()["removed_cache_entries"] == 0
        assert file.exists()
        with pytest.raises(StorageError):
            storage.ensure_space()
    assert storage.maintain()["removed_cache_entries"] == 1


def test_protected_results_can_exhaust_budget_without_deletion(tmp_path):
    (tmp_path / "manual.fits").write_bytes(b"xx")
    storage = StorageManager(tmp_path, 1, 0)
    with pytest.raises(StorageError):
        with storage.activity():
            pass
    assert (tmp_path / "manual.fits").is_file()


def test_keyed_locks_release_reference_after_error():
    locks = KeyedLocks()
    with pytest.raises(ValueError):
        with locks.hold("result"):
            raise ValueError("controlled")
    assert locks._entries == {}
    with locks.hold("result"):
        pass
