from __future__ import annotations

from orbitlens.targets import PRESETS, get_preset, public_presets


def test_five_required_presets() -> None:
    ids = {preset.id for preset in PRESETS}
    assert ids == {"barnard", "epsindi_b", "wise0855", "rw_aur", "r_dra"}


def test_presets_are_in_catalog_range() -> None:
    for preset in PRESETS:
        assert 0 <= preset.ra_deg < 360
        assert -90 <= preset.dec_deg <= 90
        assert preset.reference
        assert preset.note


def test_lookup_by_alias_and_name() -> None:
    assert get_preset("Estrella de Barnard") is not None
    assert get_preset("epsilon indi b").id == "epsindi_b"
    assert get_preset("WISE 0855-0714").id == "wise0855"
    assert get_preset("rw aur").id == "rw_aur"
    assert get_preset("R Draconis").id == "r_dra"


def test_unknown_preset() -> None:
    assert get_preset("Planeta X") is None


def test_epsilon_indi_b_is_not_one_degree_west() -> None:
    import pytest

    from orbitlens.coordinates import parse_dec, parse_ra

    preset = get_preset("epsindi_b")
    assert preset.ra_deg == pytest.approx(parse_ra("22 04 10.5", sexagesimal=True))
    assert preset.dec_deg == pytest.approx(parse_dec("-56 46 57.5", sexagesimal=True), abs=1e-5)
    assert not preset.verified


def test_public_presets_hide_internal_aliases() -> None:
    public = public_presets()
    assert len(public) == 5
    assert all("aliases" not in item for item in public)
    assert all("verified" in item for item in public)
