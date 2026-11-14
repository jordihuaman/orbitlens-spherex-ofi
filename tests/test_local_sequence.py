import json

import numpy as np
import pytest
from astropy.io import fits

from orbitlens.config import Settings
from orbitlens.local_sequence import import_sequence
from orbitlens.manifest import validate_result_files
from orbitlens.pipeline import build_target_wcs


def entries(tmp_path, count=3):
    result = []
    wcs, width, height = build_target_wcs(10, 20, 2)
    for index in range(count):
        header = wcs.to_header()
        header["OBSID"] = f"local-{index}"
        header["MJD-OBS"] = 61000 + index
        header["DETECTOR"] = 2
        header["BUNIT"] = "MJy/sr"
        primary = fits.PrimaryHDU()
        primary.header["VERSION"] = "fixture"
        path = tmp_path / f"{index}.fits"
        fits.HDUList([primary, fits.ImageHDU(np.ones((height, width)), header=header, name="IMAGE")]).writeto(path)
        result.append({"path": path, "source_url": f"https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/{index}.fits"})
    return result


def test_local_sequence_sorted_uses_fits_times_and_never_downloads(tmp_path, monkeypatch):
    import httpx

    def forbidden(*args, **kwargs):
        raise AssertionError("una importación local no debe consultar red")

    monkeypatch.setattr(httpx.Client, "send", forbidden)
    settings = Settings(data_dir=tmp_path / "data")
    inputs = entries(tmp_path)[::-1]
    job = import_sequence(inputs, 10, 20, 2, settings)
    assert job.status == "ready"
    root = settings.data_dir / "results" / job.result_id
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["search"]["method"] == "local-sequence-import"
    assert manifest["search"]["queried_at"] is None
    assert manifest["search"]["origin_verified"] is False
    assert [f["time"]["t_min_mjd"] for f in manifest["frames"]] == [61000, 61001, 61002]
    validate_result_files(root, manifest)
    assert import_sequence(inputs, 10, 20, 2, settings).result_id == job.result_id


def test_two_imported_frames_remain_partial(tmp_path):
    job = import_sequence(entries(tmp_path, 2), 10, 20, 2, Settings(data_dir=tmp_path / "data"))
    assert job.status == "partial"


@pytest.mark.parametrize("damage", ["qr2", "duplicate", "hash", "mixed-detector", "wrong-field", "nan-time"])
def test_invalid_local_sequence_is_rejected(tmp_path, damage):
    inputs = entries(tmp_path)
    ra = 10
    if damage == "qr2":
        inputs[0]["source_url"] = inputs[0]["source_url"].replace("dr1", "qr2")
    elif damage == "duplicate":
        inputs[1] = inputs[0]
    elif damage == "hash":
        inputs[0]["sha256"] = "0" * 64
    elif damage == "wrong-field":
        ra = 100
    else:
        with fits.open(inputs[0]["path"], mode="update") as hdul:
            hdul["IMAGE"].header["DETECTOR" if damage == "mixed-detector" else "MJD-OBS"] = (3 if damage == "mixed-detector" else "nan")
    with pytest.raises((ValueError, RuntimeError)):
        import_sequence(inputs, ra, 20, 2, Settings(data_dir=tmp_path / "data"))
    assert not list((tmp_path / "data").glob("results/*/manifest.json"))
