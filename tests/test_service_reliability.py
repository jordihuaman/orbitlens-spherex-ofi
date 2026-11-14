"""Integración del pipeline con FITS sintéticos y proveedor sin red."""

import json

import numpy as np
import pytest
from astropy.io import fits

from orbitlens.config import Settings
from orbitlens.irsa_client import SearchOutcome, SiaRecord
from orbitlens.jobs import Job
from orbitlens.manifest import validate_result_files
from orbitlens.pipeline import build_target_wcs
from orbitlens.service import SearchService, select_spread


@pytest.fixture
def pipeline(tmp_path):
    records = [SiaRecord(obs_id=f"obs-{index}", collection="spherex_dr1",
                         access_url=f"https://irsa.ipac.caltech.edu/{index}.fits",
                         bandpass="SPHEREx-D2", t_min=61000 + index)
               for index in range(5)]
    state = {"records": records, "warnings": [], "fail": set(), "tiny": False, "downloads": [], "searches": 0}

    def search(*args, **kwargs):
        state["searches"] += 1
        return SearchOutcome(records=list(state["records"]), warnings=list(state["warnings"]),
                             collections=["spherex_dr1", "spherex_qr3"])

    def download(client, url, destination, **kwargs):
        state["downloads"].append(url)
        if destination.stem in state["fail"]:
            raise ValueError("fallo controlado de candidato")
        destination.parent.mkdir(parents=True, exist_ok=True)
        wcs, width, height = build_target_wcs(10, 20, 1)
        if state["tiny"]:
            wcs.wcs.cdelt *= 0.1
        header = wcs.to_header()
        header["DETECTOR"] = 2
        header["BUNIT"] = "MJy/sr"
        header.update(state.get("metadata", {}))
        primary = fits.PrimaryHDU()
        primary.header["VERSION"] = "fixture"
        fits.HDUList([primary, fits.ImageHDU(
            data=np.ones((height, width)), header=header, name="IMAGE",
        )]).writeto(destination, overwrite=True)
        return destination

    service = SearchService(Settings(data_dir=tmp_path, max_candidates=5),
                            search_fn=search, download_fn=download)
    request = {"ra_deg": 10, "dec_deg": 20, "fov_arcmin": 1, "frames": 3, "detector": "D2"}
    try:
        yield service, request, state
    finally:
        service.close()


def run(service, request, name="test"):
    job = Job(id=name, request=request)
    service.run(job, request)
    path = service.results_dir / job.result_id if job.result_id else None
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8")) if path else None
    return job, path, manifest


def test_partial_cache_is_not_promoted_to_ready(pipeline):
    service, request, state = pipeline
    state["records"] = state["records"][:2]
    first, _, _ = run(service, request, "first")
    second, _, manifest = run(service, request, "second")
    assert first.result_id == second.result_id
    assert first.status == second.status == manifest["status"] == "partial"
    assert any("reutilizado" in warning for warning in second.warnings)


@pytest.mark.parametrize("damage", ["corrupt-png", "missing-original"])
def test_corrupt_cache_is_regenerated(pipeline, damage):
    service, request, _ = pipeline
    first, path, manifest = run(service, request, "first")
    frame = manifest["frames"][0]
    if damage == "corrupt-png":
        image = path / frame["png"]
        data = image.read_bytes()
        image.write_bytes(bytes([data[0] ^ 1]) + data[1:])
    else:
        (path / frame["original_fits"]).unlink()
    with pytest.raises(ValueError):
        validate_result_files(path, manifest)
    second, path, manifest = run(service, request, "second")
    assert first.result_id == second.result_id
    assert second.status == "ready"
    validate_result_files(path, manifest)
    assert not any("reutilizado" in warning for warning in second.warnings)


def test_failed_candidate_gets_replacement_and_frames_stay_ordered(pipeline):
    service, request, state = pipeline
    state["fail"] = {"obs-2"}
    job, path, manifest = run(service, request)
    assert job.status == "partial"  # Se conservan avisos aunque haya sustituto.
    assert len(manifest["frames"]) == 3
    assert [frame["obs_id"] for frame in manifest["frames"]] == ["obs-0", "obs-1", "obs-4"]
    assert manifest["search"]["attempted"] == 4
    assert len(manifest["search"]["failures"]) == 1
    assert len(manifest["files"]) == 9  # PNG, derivado y original por frame.
    assert all(frame["access_url"].startswith("https://irsa.") for frame in manifest["frames"])
    validate_result_files(path, manifest)


def test_partial_collection_failure_is_partial_even_with_three_frames(pipeline):
    service, request, state = pipeline
    state["warnings"] = ["SIA spherex_qr3: HTTP 502"]
    job, _, manifest = run(service, request)
    assert job.status == "partial"
    assert manifest["search"]["failed_collections"] == ["spherex_qr3"]


def test_incomplete_empty_search_is_error_not_confirmed_empty(pipeline):
    service, request, state = pipeline
    state["records"] = []
    state["warnings"] = ["SIA spherex_qr3: HTTP 502"]
    job, _, _ = run(service, request)
    assert job.status == "error"
    assert job.result_id is None


def test_quality_threshold_is_applied_after_reprojection(pipeline):
    service, request, state = pipeline
    state["tiny"] = True
    job, _, _ = run(service, request)
    assert job.status == "error"
    assert any("cobertura válida de salida" in warning for warning in job.warnings)
    assert len(state["downloads"]) <= service.settings.max_candidates


def test_spread_with_single_requested_frame_has_no_division_by_zero(pipeline):
    _, _, state = pipeline
    assert select_spread(state["records"], 1) == state["records"][:1]


def test_empty_cache_expires_after_sixty_seconds(pipeline):
    import os
    import time

    service, request, state = pipeline
    records = state["records"]
    state["records"] = []
    assert run(service, request)[0].status == "empty"
    assert run(service, request)[0].status == "empty"
    assert state["searches"] == 1
    cache_path = next(service.cache.root.glob("sia/*/search.json"))
    os.utime(cache_path, (time.time() - 61, time.time() - 61))
    state["records"] = records
    assert run(service, request)[0].status == "ready"
    assert state["searches"] == 2


def test_partial_failure_is_not_cached_as_success(pipeline):
    service, request, state = pipeline
    state["warnings"] = ["SIA spherex_qr3: HTTP 502"]
    assert run(service, request)[0].status == "partial"
    state["warnings"] = []
    assert run(service, request)[0].status == "ready"
    assert state["searches"] == 2


def test_same_exposure_is_not_counted_twice_across_collections(pipeline):
    from dataclasses import replace

    service, request, state = pipeline
    records = state["records"][:2]
    state["records"] = [*records, replace(records[0], collection="spherex_dr1_deep")]
    job, _, manifest = run(service, request)
    assert job.status == "partial"
    assert len(manifest["frames"]) == 2
    assert manifest["search"]["duplicate_exposures"] == 1


def test_stale_records_after_total_outage_remain_partial(pipeline):
    import os
    import time

    service, request, state = pipeline
    assert run(service, request)[0].status == "ready"
    cache_path = next(service.cache.root.glob("sia/*/search.json"))
    old = time.time() - 25 * 3600
    os.utime(cache_path, (old, old))
    state["warnings"] = ["SIA spherex_dr1: HTTP 503", "SIA spherex_qr3: HTTP 503"]
    job, _, manifest = run(service, request)
    assert job.status == "partial"
    assert manifest["search"]["failed_collections"] == ["spherex_dr1", "spherex_qr3"]
    assert any("anterior en caché" in warning for warning in job.warnings)


def test_stale_empty_cannot_confirm_no_coverage_during_outage(pipeline):
    import os
    import time

    service, request, state = pipeline
    state["records"] = []
    assert run(service, request)[0].status == "empty"
    cache_path = next(service.cache.root.glob("sia/*/search.json"))
    old = time.time() - 61
    os.utime(cache_path, (old, old))
    state["warnings"] = ["SIA spherex_dr1: HTTP 503", "SIA spherex_qr3: HTTP 503"]
    with pytest.raises(RuntimeError, match="todas las colecciones IRSA fallaron"):
        run(service, request)


@pytest.mark.parametrize("metadata", [{"OBSID": "wrong-observation"}, {"MJD-OBS": 50000}, {"DETECTOR": 9}])
def test_fits_metadata_cannot_contradict_sia(pipeline, metadata):
    service, request, state = pipeline
    state["metadata"] = metadata
    job, _, _ = run(service, request)
    assert job.status == "error"
    assert job.result_id is None
    assert any("contradice" in warning or "detector reconocible" in warning for warning in job.warnings)


def test_corrupt_original_cache_is_downloaded_again(pipeline):
    service, request, state = pipeline
    assert run(service, request)[0].status == "ready"
    downloads = len(state["downloads"])
    raw = next(service.cache.root.glob("cutout/*/*.fits"))
    data = raw.read_bytes()
    raw.write_bytes(b"BROKEN" + data[6:])
    assert run(service, request)[0].status == "ready"
    assert len(state["downloads"]) == downloads + 1
