from __future__ import annotations

import httpx
import pytest

from orbitlens.config import Settings
from orbitlens.irsa_client import (
    IrsaError,
    SiaRecord,
    build_sia_params,
    parse_sia_votable,
    search,
    search_radius_deg,
)

VOTABLE = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
 <RESOURCE type="results">
  <INFO name="QUERY_STATUS" value="OK"/>
  <TABLE>
   <FIELD name="obs_id" datatype="char" arraysize="*"/>
   <FIELD name="obs_collection" datatype="char" arraysize="*"/>
   <FIELD name="access_url" datatype="char" arraysize="*"/>
   <FIELD name="energy_bandpassname" datatype="char" arraysize="*"/>
   <FIELD name="t_min" datatype="double" unit="d"/>
   <FIELD name="t_max" datatype="double" unit="d"/>
   <DATA><TABLEDATA>
    <TR><TD>obs-1</TD><TD>spherex_dr1</TD><TD>https://irsa.ipac.caltech.edu/ibe/data/spherex/a.fits</TD><TD>D1</TD><TD>61000.1</TD><TD>61000.2</TD></TR>
    <TR><TD>obs-2</TD><TD>spherex_qr3</TD><TD>https://irsa.ipac.caltech.edu/ibe/data/spherex/b.fits</TD><TD>D2</TD><TD>61010.1</TD><TD>61010.2</TD></TR>
   </TABLEDATA></DATA>
  </TABLE>
 </RESOURCE>
</VOTABLE>"""

OVERFLOW_VOTABLE = VOTABLE.replace(b'value="OK"', b'value="OVERFLOW"')


def test_build_sia_params() -> None:
    params = build_sia_params("spherex_dr1", 10.0, -20.0, 0.15, maxrec=10)
    assert params["COLLECTION"] == "spherex_dr1"
    assert params["POS"] == "CIRCLE 10.00000000 -20.00000000 0.15000000"
    assert params["RESPONSEFORMAT"] == "VOTABLE"
    assert params["MAXREC"] == "10"


def test_search_radius_uses_full_width() -> None:
    assert search_radius_deg(10.0) == pytest.approx(0.1296, rel=1e-3)


def test_parse_votable() -> None:
    records, overflow = parse_sia_votable(VOTABLE)
    assert not overflow
    assert len(records) == 2
    assert records[0].obs_id == "obs-1"
    assert records[0].t_min == pytest.approx(61000.1)
    assert records[1].bandpass == "D2"


def test_parse_overflow_info() -> None:
    records, overflow = parse_sia_votable(OVERFLOW_VOTABLE)
    assert overflow
    assert len(records) == 2


def test_parse_invalid_votable() -> None:
    with pytest.raises(IrsaError):
        parse_sia_votable(b"<html>error</html>")


def test_http_200_votable_error_is_not_empty_success():
    content = VOTABLE.replace(b'value="OK"', b'value="ERROR"')
    with pytest.raises(IrsaError, match="QUERY_STATUS=ERROR"):
        parse_sia_votable(content)


def test_missing_mandatory_column_is_not_empty_success():
    content = VOTABLE.replace(b'name="access_url"', b'name="wrong_column"')
    with pytest.raises(IrsaError, match="columnas obligatorias"):
        parse_sia_votable(content)


def test_irsa_ids_differ_from_column_names():
    content = VOTABLE.replace(b'name="obs_id"', b'ID="col_9" name="obs_id"')
    content = content.replace(b'name="access_url"', b'ID="col_15" name="access_url"')
    content = content.replace(b'name="t_min"', b'ID="col_39" name="t_min"')
    records, _ = parse_sia_votable(content)
    assert records[0].obs_id == "obs-1"
    assert records[0].t_min == pytest.approx(61000.1)
    assert records[0].access_url.startswith("https://irsa.ipac.caltech.edu/")


def test_cutout_url_preserves_query_and_replaces_size() -> None:
    record = SiaRecord(
        obs_id="obs-1",
        collection="spherex_dr1",
        access_url="https://irsa.ipac.caltech.edu/ibe/data/x.fits?foo=bar&size=1deg",
    )
    url = record.cutout_url(
        10.0, 20.0, 0.1667, allowed_hosts=("irsa.ipac.caltech.edu",)
    )
    assert "foo=bar" in url
    assert "center=10.00000000%2C20.00000000deg" in url
    assert "size=0.16670000deg" in url
    assert "size=1deg" not in url


def test_cutout_url_rejects_untrusted_host() -> None:
    record = SiaRecord(
        obs_id="obs-1",
        collection="spherex_dr1",
        access_url="https://evil.example/data.fits",
    )
    with pytest.raises(IrsaError):
        record.cutout_url(1, 2, 0.1, allowed_hosts=("irsa.ipac.caltech.edu",))


class _FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=httpx.Request("GET", "https://example"), response=None
            )


class _FakeClient(httpx.Client):
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        super().__init__(transport=httpx.MockTransport(self._respond))

    def _respond(self, request):
        result = self.responses[request.url.params["COLLECTION"]]
        if isinstance(result, Exception):
            raise result
        return httpx.Response(result.status_code, content=result.content)


def test_search_merges_and_deduplicates() -> None:
    settings = Settings(retry_backoff_s=0.0)
    client = _FakeClient(
        {
            "spherex_dr1": _FakeResponse(VOTABLE),
            "spherex_qr3": _FakeResponse(VOTABLE),
            "spherex_dr1_deep": httpx.ConnectError("sin red"),
            "spherex_qr3_deep": _FakeResponse(VOTABLE),
        }
    )
    outcome = search(client, settings, 10.0, 20.0, 10.0)
    assert len(outcome.records) == 2
    assert any("sin red" in warning for warning in outcome.warnings)
    assert outcome.collections == list(settings.collections)


class _FlakyClient(httpx.Client):
    def __init__(self, failures: int, response: _FakeResponse) -> None:
        self.failures = failures
        self.response = response
        self.calls = 0
        super().__init__(transport=httpx.MockTransport(self._respond))

    def _respond(self, request):
        self.calls += 1
        if self.calls <= self.failures:
            raise httpx.ConnectError("fallo transitorio")
        return httpx.Response(self.response.status_code, content=self.response.content)


def test_query_collection_retries_transient_failure() -> None:
    from orbitlens.irsa_client import query_collection

    settings = Settings(retry_attempts=2, retry_backoff_s=0.0)
    client = _FlakyClient(1, _FakeResponse(VOTABLE))
    records, overflow = query_collection(
        client, settings, "spherex_dr1", 10.0, 20.0, 0.1
    )
    assert client.calls == 2
    assert len(records) == 2
    assert not overflow
