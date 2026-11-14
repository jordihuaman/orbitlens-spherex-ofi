from __future__ import annotations

import json

import numpy as np
import pytest
from astropy.io import fits

from orbitlens.config import Settings
from orbitlens.manifest import sha256_file
from orbitlens.pipeline import PipelineError, build_target_wcs
from scripts.import_irsa_cutout import publish

SOURCE = "https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/test.fits?center=10,20&size=0.02"


def make_fits(tmp_path):
    wcs, width, height = build_target_wcs(10, 20, 1.2)
    header = wcs.to_header()
    for key, value in {"OBSID": "test", "DETECTOR": 1, "BUNIT": "MJy/sr",
                       "MJD-OBS": 61000}.items():
        header[key] = value
    primary = fits.PrimaryHDU()
    primary.header["VERSION"] = "fixture"
    path = tmp_path / "input.fits"
    fits.HDUList([primary, fits.ImageHDU(data=np.ones((height, width)),
                                       header=header, name="IMAGE")]).writeto(path)
    return path


def test_import_publishes_original_and_records_real_metadata(tmp_path):
    path = make_fits(tmp_path)
    manifest_path = publish(path, SOURCE, 10, 20, 1.2, Settings(data_dir=tmp_path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["search"]["method"] == "local-import"
    assert manifest["frames"][0]["time"]["t_min_mjd"] == 61000
    assert manifest["frames"][0]["detector"] == "D1"
    assert manifest["inspection"]["original_sha256"] == sha256_file(path)
    for item in manifest["files"]:
        assert sha256_file(manifest_path.parent / item["path"]) == item["sha256"]


@pytest.mark.parametrize("url", ["https://evil.example/dr1.fits",
                                "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/level2/test.fits"])
def test_import_rejects_unknown_origin_and_qr2(tmp_path, url):
    with pytest.raises(ValueError):
        publish(make_fits(tmp_path), url, 10, 20, 1.2, Settings(data_dir=tmp_path))
    assert not list(tmp_path.glob("results/*/manifest.json"))


def test_import_rejects_wrong_field(tmp_path):
    with pytest.raises(PipelineError, match="fuera del recorte"):
        publish(make_fits(tmp_path), SOURCE, 100, 20, 1.2, Settings(data_dir=tmp_path))
