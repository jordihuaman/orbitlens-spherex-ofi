import math

import pytest
from astropy.coordinates import SkyCoord

from orbitlens.astrometry import SNAPSHOT, position_at


@pytest.mark.parametrize("target", list(SNAPSHOT["entries"]))
def test_catalog_position_at_reference_epoch(target):
    ra, dec = position_at(target, 2000)
    assert ra == pytest.approx(SNAPSHOT["entries"][target]["ra_deg"])
    assert dec == pytest.approx(SNAPSHOT["entries"][target]["dec_deg"])


def test_pmra_includes_cosdec_and_high_motion_is_not_ignored():
    entry = SNAPSHOT["entries"]["epsindi_b"]
    ra, dec = position_at("epsindi_b", 2026)
    separation = SkyCoord(ra, dec, unit="deg").separation(SkyCoord(entry["ra_deg"], entry["dec_deg"], unit="deg")).arcsec
    expected = math.hypot(entry["pmra"], entry["pmdec"]) * 26 / 1000
    assert separation == pytest.approx(expected, abs=0.001)
    assert ra > entry["ra_deg"] and dec < entry["dec_deg"]


@pytest.mark.parametrize("epoch", [float("nan"), float("inf"), 1800, 2200])
def test_invalid_epoch_rejected(epoch):
    with pytest.raises(ValueError):
        position_at("barnard", epoch)
