from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from orbitlens.pipeline import (
    ProcessedFrame,
    SpherexImage,
    apply_colormap,
    asinh_stretch,
    build_target_wcs,
    compute_stretch_limits,
    read_spherex_image,
    render_rgba,
    reproject_frame,
    write_derived_fits,
    write_png,
)


def _celestial_header(shape: tuple[int, int], *, crval=(10.0, 20.0)) -> fits.Header:
    height, width = shape
    wcs = WCS(naxis=2)
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    wcs.wcs.cunit = ["deg", "deg"]
    wcs.wcs.crval = list(crval)
    wcs.wcs.crpix = [(width + 1) / 2, (height + 1) / 2]
    wcs.wcs.cdelt = [-0.001, 0.001]
    return wcs.to_header()


def _write_fits(tmp_path, data: np.ndarray, flags: np.ndarray | None = None):
    header = _celestial_header(data.shape)
    header["DETECTOR"] = "D1"
    header["VERSION"] = "7.0"
    header["BUNIT"] = "MJy/sr"

    hdus = [fits.PrimaryHDU()]
    hdus.append(fits.ImageHDU(data=data, header=header, name="IMAGE"))
    if flags is not None:
        flag_header = fits.Header()
        flag_header["MSKN0"] = "HOT"
        flag_header["MSKD0"] = "hot pixel"
        flag_header["MSKN1"] = "SOURCE"
        flag_header["MSKD1"] = "source"
        hdus.append(fits.ImageHDU(data=flags, header=flag_header, name="FLAGS"))
    path = tmp_path / "cutout.fits"
    fits.HDUList(hdus).writeto(path)
    return path


def test_build_target_wcs_is_north_up_east_left() -> None:
    wcs, width, height = build_target_wcs(269.45208, 4.69339, 10.0)
    assert width == height == 98
    assert wcs.wcs.crval.tolist() == pytest.approx([269.45208, 4.69339])
    assert wcs.wcs.cdelt[0] < 0 < wcs.wcs.cdelt[1]
    assert [str(ctype).strip() for ctype in wcs.wcs.ctype] == ["RA---TAN", "DEC--TAN"]


def test_read_spherex_image_applies_flags(tmp_path) -> None:
    data = np.ones((20, 20), dtype=np.float64)
    flags = np.zeros((20, 20), dtype=np.int64)
    flags[0, 0] = 1  # HOT
    path = _write_fits(tmp_path, data, flags)

    image = read_spherex_image(path)
    assert image.data.shape == (20, 20)
    assert not image.valid[0, 0]
    assert image.valid_fraction == pytest.approx(399 / 400)
    assert image.detector == "D1"
    assert image.version == "7.0"
    assert image.lambda_um is None
    assert any("longitud de onda" in warning for warning in image.warnings)


def test_read_spherex_image_rejects_cube(tmp_path) -> None:
    cube = np.ones((3, 10, 10), dtype=np.float64)
    path = tmp_path / "cube.fits"
    fits.HDUList(
        [
            fits.PrimaryHDU(),
            fits.ImageHDU(data=cube, header=_celestial_header((10, 10)), name="IMAGE"),
        ]
    ).writeto(path)
    with pytest.raises(Exception, match="2D"):
        read_spherex_image(path)


def test_reproject_identity_grid_preserves_values(tmp_path) -> None:
    data = np.arange(400, dtype=np.float64).reshape(20, 20)
    path = _write_fits(tmp_path, data)
    image = read_spherex_image(path)

    processed = reproject_frame(image, image.wcs, image.data.shape)
    assert processed.data.shape == image.data.shape
    assert np.allclose(processed.data, data, equal_nan=True, atol=1e-6)
    assert processed.valid_fraction == pytest.approx(1.0)


def test_stretch_is_monotonic_and_normalized() -> None:
    data = np.array([[0.0, 5.0, 10.0]])
    valid = np.array([[True, True, True]])
    stretched = asinh_stretch(data, valid, 0.0, 10.0)
    assert stretched[0, 0] == pytest.approx(0.0)
    assert stretched[0, 2] == pytest.approx(1.0)
    assert stretched[0, 0] < stretched[0, 1] < stretched[0, 2]


def test_stretch_marks_invalid_pixels_zero() -> None:
    data = np.array([[1.0, 2.0]])
    valid = np.array([[True, False]])
    stretched = asinh_stretch(data, valid, 0.0, 2.0)
    assert stretched[0, 1] == 0.0


def test_compute_stretch_limits_uses_global_valid_pixels() -> None:
    first = ProcessedFrame(
        source=_dummy_image(),
        data=np.array([[0.0, 10.0], [np.nan, np.nan]]),
        valid=np.array([[True, True], [False, False]]),
    )
    second = ProcessedFrame(
        source=_dummy_image(),
        data=np.array([[20.0, 30.0], [40.0, 50.0]]),
        valid=np.ones((2, 2), dtype=bool),
    )
    vmin, vmax = compute_stretch_limits([first, second], low_percentile=0, high_percentile=100)
    assert vmin == pytest.approx(0.0)
    assert vmax == pytest.approx(50.0)


def test_colormap_alpha_follows_validity() -> None:
    values = np.array([[0.0, 1.0]])
    valid = np.array([[True, False]])
    rgba = apply_colormap(values, valid)
    assert rgba.shape == (1, 2, 4)
    assert rgba[0, 0, 3] == 255
    assert rgba[0, 1, 3] == 0


def test_render_and_write_outputs(tmp_path) -> None:
    data = np.linspace(0, 1, 100).reshape(10, 10)
    image = _dummy_image()
    frame = ProcessedFrame(source=image, data=data, valid=np.ones((10, 10), bool))
    rgba = render_rgba(frame, 0.0, 1.0)
    png = tmp_path / "frame.png"
    write_png(rgba, png)
    assert png.stat().st_size > 0

    fits_path = tmp_path / "frame.fits"
    wcs, _, _ = build_target_wcs(10.0, 20.0, 1.0)
    write_derived_fits(data, wcs, fits_path, metadata={"OBSID": "abc"})
    with fits.open(fits_path) as hdul:
        assert hdul[0].data.shape == (10, 10)
        assert hdul[0].header["OBSID"] == "abc"


def _dummy_image() -> SpherexImage:
    from orbitlens.masks import FlagDefinitions

    return SpherexImage(
        path=Path("dummy.fits"),
        data=np.zeros((2, 2)),
        flags=None,
        header=fits.Header(),
        wcs=WCS(naxis=2),
        flag_definitions=FlagDefinitions(bits={}, source="none"),
        valid=np.ones((2, 2), dtype=bool),
        valid_fraction=1.0,
        center_valid=True,
        lambda_um=None,
        bandwidth_um=None,
        detector="D1",
        version="1",
        bunit="MJy/sr",
    )
