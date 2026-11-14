"""Contrato del verificador con proveedor controlado; NO son datos reales."""

import json
import runpy
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits

from orbitlens.irsa_client import SearchOutcome, SiaRecord
from orbitlens.manifest import sha256_file
from orbitlens.pipeline import build_target_wcs
from orbitlens.targets import get_preset


def test_verifier_publishes_original_derived_and_manifest(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts" / "verify_real_data.py"
    main = runpy.run_path(str(script))["main"]
    monkeypatch.setenv("ORBITLENS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [str(script), "--target", "epsindi_b",
                                    "--download", "--detector", "D2", "--fov", "1"])
    item = SiaRecord(obs_id="fixture", collection="spherex_dr1", bandpass="SPHEREx-D2",
                     access_url="https://irsa.ipac.caltech.edu/fixture.fits", t_min=61000)

    def search(*args, **kwargs):
        return SearchOutcome(records=[item], collections=["spherex_dr1"])

    def download(client, url, path, **kwargs):
        preset = get_preset("epsindi_b")
        wcs, width, height = build_target_wcs(preset.ra_deg, preset.dec_deg, 1)
        header = wcs.to_header()
        header["DETECTOR"] = "D2"
        header["BUNIT"] = "MJy/sr"
        fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(
            data=np.ones((height, width)), header=header, name="IMAGE",
        )]).writeto(path)
        return path

    monkeypatch.setitem(main.__globals__, "search", search)
    monkeypatch.setitem(main.__globals__, "download_to_file", download)
    assert main() == 0
    manifest_path, = tmp_path.glob("results/*/manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["search"]["detector_selected"] == "D2"
    assert manifest["frames"][0]["collection"] == "spherex_dr1"
    assert manifest["request"]["verified"] is False
    assert len(manifest["files"]) == 3
    for entry in manifest["files"]:
        assert sha256_file(manifest_path.parent / entry["path"]) == entry["sha256"]


def test_verifier_does_not_publish_success_without_records(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts" / "verify_real_data.py"
    main = runpy.run_path(str(script))["main"]
    monkeypatch.setenv("ORBITLENS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [str(script), "--download"])

    def search(*args, **kwargs):
        return SearchOutcome(records=[], collections=["spherex_dr1"], warnings=["SIA: HTTP 502"])

    monkeypatch.setitem(main.__globals__, "search", search)
    assert main() == 1
    assert not list(tmp_path.glob("results/*/manifest.json"))
