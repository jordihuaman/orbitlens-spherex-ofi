from __future__ import annotations

import numpy as np
from astropy.io import fits

from orbitlens.masks import (
    FlagDefinitions,
    compute_valid_mask,
    parse_flag_bits,
    resolve_flag_bits,
)


def test_parse_flag_bits_from_header() -> None:
    header = fits.Header()
    header["MSKN0"] = "HOT"
    header["MSKD0"] = "hot pixel"
    header["MSKN1"] = "SOURCE"
    header["MSKD1"] = "source"
    assert parse_flag_bits(header) == {"HOT": 0, "SOURCE": 1}


def test_parse_flag_bits_falls_back_to_description() -> None:
    header = fits.Header()
    header["MSKD0"] = "HOT"
    assert parse_flag_bits(header) == {"HOT": 0}


def test_parse_flag_bits_ignores_numeric_values() -> None:
    header = fits.Header()
    header["MSKN0"] = 3
    header["MSKD0"] = "HOT"
    assert parse_flag_bits(header) == {"HOT": 0}


def test_compute_valid_mask_rejects_defined_bits() -> None:
    definitions = FlagDefinitions(bits={"HOT": 0, "SOURCE": 1}, source="header")
    flags = np.array([[0, 1, 2, 3]], dtype=np.int64)
    valid = compute_valid_mask(flags, definitions)
    assert valid.tolist() == [[True, False, True, False]]


def test_source_bit_alone_remains_valid() -> None:
    definitions = FlagDefinitions(bits={"HOT": 0, "SOURCE": 1}, source="header")
    flags = np.array([[1, 2]], dtype=np.int64)
    valid = compute_valid_mask(flags, definitions)
    assert valid.tolist() == [[False, True]]


def test_no_definitions_only_rejects_non_finite() -> None:
    definitions = resolve_flag_bits(fits.Header())
    assert definitions.bits == {}
    assert definitions.source == "none"
    flags = np.array([[0.0, np.nan, -1.0, np.inf]])
    valid = compute_valid_mask(flags, definitions)
    assert valid.tolist() == [[True, False, False, False]]


def test_resolve_warns_about_missing_names() -> None:
    header = fits.Header()
    header["MSKN0"] = "HOT"
    header["MSKD0"] = "hot"
    definitions = resolve_flag_bits(header)
    assert definitions.bits == {"HOT": 0}
    assert definitions.warnings
