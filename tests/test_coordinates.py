from __future__ import annotations

import math

import pytest

from orbitlens.coordinates import (
    CoordinateError,
    format_sexagesimal,
    parse_dec,
    parse_pair,
    parse_ra,
    validate_dec,
    validate_ra,
)


def test_decimal_coordinates_valid() -> None:
    assert parse_ra("133.79512") == pytest.approx(133.79512)
    assert parse_dec("-7.24514") == pytest.approx(-7.24514)
    assert parse_pair(269.45208, 4.69339) == pytest.approx((269.45208, 4.69339))


@pytest.mark.parametrize("value", [-1, 360, 720, float("nan"), float("inf")])
def test_ra_out_of_range(value: float) -> None:
    with pytest.raises(CoordinateError):
        validate_ra(value)


@pytest.mark.parametrize("value", [-90.1, 90.1, float("nan"), float("-inf")])
def test_dec_out_of_range(value: float) -> None:
    with pytest.raises(CoordinateError):
        validate_dec(value)


def test_sexagesimal_ra_uses_hours() -> None:
    ra = parse_ra("17 57 48.5", sexagesimal=True)
    assert ra == pytest.approx(269.45208333, abs=1e-8)
    assert parse_ra("17h57m48.5s", sexagesimal=True) == pytest.approx(ra)


def test_sexagesimal_dec_sign() -> None:
    assert parse_dec("-56 46 57.5", sexagesimal=True) == pytest.approx(
        -56.78263889, abs=1e-8
    )
    assert parse_dec("+04 41 36", sexagesimal=True) == pytest.approx(
        4.69333333, abs=1e-8
    )


@pytest.mark.parametrize(
    ("ra", "dec"),
    [
        ("24 00 00", "0 00 00"),
        ("12 60 00", "0 00 00"),
        ("12 00 60", "0 00 00"),
        ("-01 00 00", "0 00 00"),
    ],
)
def test_invalid_sexagesimal_ra(ra: str, dec: str) -> None:
    with pytest.raises(CoordinateError):
        parse_pair(ra, dec, sexagesimal=True)


def test_invalid_sexagesimal_dec() -> None:
    with pytest.raises(CoordinateError):
        parse_dec("90 00 01", sexagesimal=True)
    with pytest.raises(CoordinateError):
        parse_dec("91 00 00", sexagesimal=True)


def test_sexagesimal_requires_three_parts() -> None:
    with pytest.raises(CoordinateError):
        parse_ra("17 57", sexagesimal=True)


def test_format_sexagesimal_roundtrip() -> None:
    ra_text, dec_text = format_sexagesimal(269.45208, -56.78264)
    assert ra_text.startswith("17h")
    assert dec_text.startswith("-56")
    ra_again = parse_ra(ra_text, sexagesimal=True)
    dec_again = parse_dec(dec_text, sexagesimal=True)
    assert ra_again == pytest.approx(269.45208, abs=1e-3)
    assert dec_again == pytest.approx(-56.78264, abs=1e-3)


def test_non_finite_rejected() -> None:
    with pytest.raises(CoordinateError):
        parse_ra(math.nan)
    with pytest.raises(CoordinateError):
        parse_dec("nan")
