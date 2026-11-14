from __future__ import annotations

import pytest

from orbitlens.irsa_client import SiaRecord
from orbitlens.service import normalize_detector, select_detector


def test_mjd_timestamp_has_explicit_utc():
    from orbitlens.service import mjd_to_iso

    assert mjd_to_iso(61000) == "2025-11-21T00:00:00.000Z"


def record(band: str | None, instrument: str | None = None) -> SiaRecord:
    return SiaRecord(obs_id=str(band), collection="spherex_dr1",
                     access_url="https://irsa.ipac.caltech.edu/x.fits",
                     bandpass=band, instrument=instrument, t_min=61000)


@pytest.mark.parametrize("raw,expected", [("D2", "D2"), ("SPHEREx-D2", "D2"),
                                         ("spherex-d6", "D6"), ("D9", None),
                                         ("SPHEREx", None), (None, None),
                                         ("2", "D2"), (6, "D6")])
def test_detector_normalization(raw, expected):
    assert normalize_detector(raw) == expected


def test_explicit_detector_accepts_irsa_bandpass():
    records = [record("SPHEREx-D2"), record("D1"), record(None, "D2")]
    selected, detector = select_detector(records, "D2")
    assert detector == "D2"
    assert selected == [records[0], records[2]]


def test_missing_detector_never_falls_back():
    assert select_detector([record("SPHEREx-D1")], "D2") == ([], "D2")


def test_auto_selects_one_detector_deterministically():
    records = [record("D3"), record("SPHEREx-D2"), record("D3"), record("D2")]
    selected, detector = select_detector(records, "auto")
    assert detector == "D2"
    assert selected == [records[1], records[3]]
    assert select_detector(list(reversed(records)), "auto")[1] == "D2"


def test_auto_prefers_most_exposures():
    selected, detector = select_detector([record("D1"), record("D3"), record("D3")], "auto")
    assert detector == "D3"
    assert len(selected) == 2


def test_unknown_and_conflicting_metadata_are_excluded():
    assert select_detector([record(None), record("D1", "D2")], "auto") == ([], None)


@pytest.mark.parametrize("requested,expected,expected_status,fits_detector", [
    ("D2", "D2", "ready", "D2"), ("auto", "D2", "ready", "D2"),
    ("D6", None, "empty", "D2"), ("D2", "D2", "error", "D3"),
    ("D2", "D2", "ready", 2),
])
def test_service_detector_contract(tmp_path, requested, expected, expected_status, fits_detector):
    import json
    from dataclasses import replace

    import numpy as np
    from astropy.io import fits

    from orbitlens.config import PIPELINE_VERSION, Settings
    from orbitlens.irsa_client import SearchOutcome
    from orbitlens.jobs import Job
    from orbitlens.manifest import sha256_file
    from orbitlens.pipeline import build_target_wcs
    from orbitlens.service import SearchService

    records = []
    for index, band in enumerate(["D1", "SPHEREx-D2", "D2", "SPHEREx-D2"]):
        item = replace(record(band), obs_id=f"obs-{index}",
                       access_url=f"https://irsa.ipac.caltech.edu/{index}.fits",
                       t_min=61000 + index)
        records.append(item)
    calls = []

    def search(*args, **kwargs):
        return SearchOutcome(records=records, collections=["spherex_dr1"])

    def download(client, url, destination, **kwargs):
        calls.append(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        wcs, width, height = build_target_wcs(10, 20, 1)
        header = wcs.to_header()
        header["DETECTOR"] = fits_detector
        header["BUNIT"] = "MJy/sr"
        primary = fits.PrimaryHDU()
        primary.header["VERSION"] = "fixture"
        fits.HDUList([primary, fits.ImageHDU(
            data=np.ones((height, width)), header=header, name="IMAGE",
        )]).writeto(destination, overwrite=True)
        return destination

    service = SearchService(Settings(data_dir=tmp_path), search_fn=search, download_fn=download)
    job = Job(id="test", request={})
    try:
        service.run(job, {"ra_deg": 10, "dec_deg": 20, "fov_arcmin": 1,
                          "frames": 3, "detector": requested})
    finally:
        service.close()
    assert job.status == expected_status, job.public()
    if expected_status == "error":
        assert job.result_id is None
        assert any("contradice" in warning for warning in job.warnings)
        assert not list(tmp_path.glob("results/*/manifest.json"))
        return
    if expected is None:
        assert calls == []
        assert job.result_id is None
        return
    assert len(calls) == 3
    result_dir = tmp_path / "results" / job.result_id
    manifest = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["pipeline_version"] == PIPELINE_VERSION
    assert manifest["search"]["detector_requested"] == requested
    assert manifest["search"]["detector_selected"] == expected
    assert {frame["detector"] for frame in manifest["frames"]} == {expected}
    for entry in manifest["files"]:
        assert sha256_file(result_dir / entry["path"]) == entry["sha256"]
