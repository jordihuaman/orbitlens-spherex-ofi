import asyncio
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from api import create_app
from orbitlens.config import Settings
from orbitlens.downloads import DownloadError, download_to_file
from orbitlens.irsa_client import IrsaError, SiaRecord, query_collection
from orbitlens.security import RequestLimiter, SecurityMiddleware


class Service:
    def run(self, job, request):
        job.update(status="empty")


@pytest.fixture
def security_client(tmp_path):
    with TestClient(create_app(settings=Settings(data_dir=tmp_path), service=Service()), raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize("path", ["/", "/api/health", "/api/not-a-route", "/api/results/bad/manifest"])
def test_security_headers_cover_success_and_failures(security_client, path):
    response = security_client.get(path)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "unsafe-inline" not in response.headers["Content-Security-Policy"]
    assert len(response.headers["X-Request-ID"]) == 32
    assert "Strict-Transport-Security" not in response.headers
    assert response.headers["Cache-Control"] == ("no-store" if path.startswith("/api/") else "no-cache")


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json", "/.env", "/.git/config"])
def test_internal_routes_not_exposed(security_client, path):
    assert security_client.get(path).status_code == 404


def test_docs_can_be_enabled_explicitly_in_development(tmp_path):
    settings = Settings(data_dir=tmp_path, enable_docs=True)
    with TestClient(create_app(settings=settings, service=Service())) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


@pytest.mark.parametrize("host", ["evil.test", "testserver@evil.test", "testserver/evil", "testserver:999999", "testserver:0"])
def test_host_poisoning_is_rejected(security_client, host):
    assert security_client.get("/api/health", headers={"Host": host}).status_code == 400


def test_cross_site_search_is_rejected_but_explicit_dev_origin_allowed(security_client):
    request = {"target_name": "barnard"}
    assert security_client.post("/api/search", json=request, headers={"Origin": "https://evil.test"}).status_code == 403
    assert security_client.post("/api/search", json=request, headers={"Origin": "null"}).status_code == 403
    assert security_client.post("/api/search", json=request, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert security_client.post("/api/search", json=request, headers={"Origin": "http://localhost:5173"}).status_code == 202


def test_content_type_encoding_and_request_size_are_enforced(security_client):
    assert security_client.post("/api/search", content=b'{}', headers={"Content-Type": "text/plain"}).status_code == 415
    assert security_client.post("/api/search", json={}, headers={"Content-Encoding": "gzip"}).status_code == 415
    response = security_client.post("/api/search", content=b"x" * 16385, headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize("payload", [{"target_name": "barnard", "extra": "secret"},
                                     {"target_name": "x" * 129},
                                     {"ra_deg": True, "dec_deg": 20},
                                     {"ra_deg": "x" * 81, "dec_deg": 20},
                                     {"target_name": "barnard", "frames": True},
                                     {"target_name": "barnard", "sexagesimal": "yes"}])
def test_strict_input_errors_do_not_echo_payload(security_client, payload):
    response = security_client.post("/api/search", json=payload)
    assert response.status_code == 422
    for error in response.json()["detail"]:
        assert "input" not in error and "ctx" not in error


def test_unexpected_error_is_generic_and_has_security_headers(tmp_path):
    app = create_app(settings=Settings(data_dir=tmp_path), service=Service())

    @app.get("/api/boom")
    def boom():
        raise RuntimeError("private database password, D:/private/data")

    # El fallback SPA debe quedar después del endpoint deliberadamente fallido.
    app.router.routes.insert(0, app.router.routes.pop())

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/boom")
    assert response.status_code == 500
    assert "private" not in response.text and "RuntimeError" not in response.text
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"
    assert "Content-Security-Policy" in response.headers


def production_settings(tmp_path, **values):
    return Settings(data_dir=tmp_path, production=True, public_origin="https://orbitlens.example",
                    allowed_hosts=("orbitlens.example", "127.0.0.1"), cors_origins=(), **values)


def test_production_tls_hsts_and_origin_validation(tmp_path):
    app = create_app(settings=production_settings(tmp_path), service=Service())
    with TestClient(app, base_url="http://orbitlens.example") as client:
        assert client.get("/").status_code == 426
        assert client.get("/", headers={"X-Forwarded-Proto": "https"}).status_code == 426
    with TestClient(app, base_url="https://orbitlens.example") as client:
        response = client.get("/api/health")
        assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
        assert client.post("/api/search", json={"target_name": "barnard"}, headers={"Origin": "http://orbitlens.example"}).status_code == 403
        assert client.post("/api/search", json={"target_name": "barnard"}, headers={"Origin": "https://orbitlens.example"}).status_code == 202


def test_only_trusted_proxy_can_assert_tls(tmp_path):
    app = create_app(settings=production_settings(tmp_path, trusted_proxies=("10.0.0.0/8",)), service=Service())
    with TestClient(app, base_url="http://orbitlens.example", client=("10.0.0.2", 50000)) as client:
        assert client.get("/", headers={"X-Forwarded-Proto": "https"}).status_code == 200


def test_request_limiter_is_bounded_and_refills():
    now = [0.0]
    limiter = RequestLimiter(60, 2, 2, clock=lambda: now[0])
    assert limiter.admit("first") is None
    assert limiter.admit("first") is None
    assert limiter.admit("first") == 1
    assert limiter.admit("second") is None
    assert limiter.admit("third") == 30
    assert len(limiter._clients) == 2
    assert "first" not in limiter._clients
    now[0] = 121
    assert limiter.admit("third") is None


def test_http_throttle_returns_retry_after(tmp_path):
    settings = replace(Settings(data_dir=tmp_path), http_burst=1, http_requests_per_minute=1)
    with TestClient(create_app(settings=settings, service=Service())) as client:
        assert client.get("/api/health").status_code == 200
        response = client.get("/api/health")
        assert response.status_code == 429 and int(response.headers["Retry-After"]) > 0


@pytest.mark.parametrize("url", ["http://irsa.ipac.caltech.edu/file", "https://irsa.ipac.caltech.edu:444/file",
                                 "https://user:password@irsa.ipac.caltech.edu/file", "https://127.0.0.1/file",
                                 "https://irsa.ipac.caltech.edu.evil.test/file", "https://irsa.ipac.caltech.edu/file#fragment"])
def test_ssrf_invalid_origin_is_rejected_before_network(tmp_path, url):
    calls = []
    with httpx.Client(transport=httpx.MockTransport(lambda request: calls.append(request))) as client:
        with pytest.raises(ValueError):
            download_to_file(client, url, tmp_path / "file.fits", max_bytes=100,
                             allowed_hosts=("irsa.ipac.caltech.edu",))
    assert not calls
    with pytest.raises(IrsaError):
        SiaRecord(obs_id="bad", collection="spherex_dr1", access_url=url).cutout_url(10, 20, 0.1)


def test_redirect_cannot_reach_private_network_even_if_client_follows(tmp_path):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data/"})

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        with pytest.raises(DownloadError):
            download_to_file(client, "https://irsa.ipac.caltech.edu/file", tmp_path / "file.fits", max_bytes=100,
                             allowed_hosts=("irsa.ipac.caltech.edu",))
        with pytest.raises(IrsaError):
            query_collection(client, Settings(), "spherex_dr1", 10, 20, 1)
    assert len(calls) == 2 and all(url.startswith("https://irsa.ipac.caltech.edu/") for url in calls)


@pytest.mark.parametrize("case", ["chunked", "length-mismatch", "timeout"])
def test_streaming_bodies_are_bounded_before_application(case):
    async def run():
        called = []
        sent = []

        async def app(scope, receive, send):
            called.append(True)

        scope = {"type": "http", "path": "/api/search", "method": "POST", "scheme": "http",
                 "headers": [(b"host", b"testserver"), (b"content-type", b"application/json")], "query_string": b""}
        if case == "length-mismatch":
            scope["headers"].append((b"content-length", b"5"))

        async def receive():
            if case == "timeout":
                await asyncio.sleep(1)
            return {"type": "http.request", "body": b"x" * (10 if case == "chunked" else 2), "more_body": case == "chunked"}

        async def send(message):
            sent.append(message)

        await SecurityMiddleware(app, Settings(max_request_bytes=8, request_body_timeout_s=0.001))(scope, receive, send)
        assert not called
        assert sent[0]["status"] == {"chunked": 413, "length-mismatch": 400, "timeout": 408}[case]

    asyncio.run(run())


def test_security_contact_requires_real_configuration(security_client, tmp_path):
    assert security_client.get("/.well-known/security.txt").status_code == 404
    settings = Settings(data_dir=tmp_path, security_contact="mailto:security@example.test")
    with TestClient(create_app(settings=settings, service=Service())) as client:
        response = client.get("/.well-known/security.txt")
        assert response.status_code == 200 and "Expires:" in response.text


def test_unsafe_production_settings_fail_closed(tmp_path):
    with pytest.raises(ValueError):
        Settings(production=True)
    with pytest.raises(ValueError):
        production_settings(tmp_path, enable_docs=True)
    with pytest.raises(ValueError):
        Settings(allowed_hosts=("*",))
    with pytest.raises(ValueError):
        Settings(security_contact="mailto:owner@example.test\nContact: injected")


def test_cache_policy_separates_api_assets_and_html():
    from orbitlens.security import cache_control_for

    assert cache_control_for("/api/health") == "no-store"
    assert cache_control_for("/assets/index-abc123.js") == "public, max-age=31536000, immutable"
    assert cache_control_for("/") == "no-cache"


def test_missing_asset_is_not_cached_as_immutable(security_client):
    response = security_client.get("/assets/no-existe.js")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"


def test_conflicting_body_framing_is_rejected_before_application():
    async def run():
        called, sent = [], []

        async def app(scope, receive, send):
            called.append(True)

        scope = {
            "type": "http", "path": "/api/search", "method": "POST", "scheme": "http",
            "headers": [(b"host", b"testserver"), (b"content-type", b"application/json"),
                        (b"content-length", b"2"), (b"transfer-encoding", b"chunked")],
            "query_string": b"",
        }

        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        async def send(message):
            sent.append(message)

        await SecurityMiddleware(app, Settings())(scope, receive, send)
        assert not called
        assert sent[0]["status"] == 400

    asyncio.run(run())


def test_from_env_fails_closed_without_public_origin(monkeypatch):
    monkeypatch.setenv("ORBITLENS_PRODUCTION", "true")
    monkeypatch.delenv("ORBITLENS_PUBLIC_ORIGIN", raising=False)
    with pytest.raises(ValueError, match="public_origin"):
        Settings.from_env()


def test_from_env_accepts_complete_public_profile(monkeypatch):
    monkeypatch.setenv("ORBITLENS_PRODUCTION", "true")
    monkeypatch.setenv("ORBITLENS_PUBLIC_ORIGIN", "https://orbitlens.example")
    monkeypatch.setenv("ORBITLENS_ALLOWED_WEB_HOSTS", "orbitlens.example,localhost")
    monkeypatch.setenv("ORBITLENS_SECURITY_CONTACT", "mailto:security@example.test")
    monkeypatch.delenv("ORBITLENS_CORS_ORIGINS", raising=False)
    settings = Settings.from_env()
    assert settings.production is True
    assert settings.cors_origins == ()
    assert settings.public_origin == "https://orbitlens.example"
    assert settings.enable_docs is False


def test_from_env_rejects_wildcard_hosts(monkeypatch):
    monkeypatch.setenv("ORBITLENS_ALLOWED_WEB_HOSTS", "*")
    with pytest.raises(ValueError, match="hosts concretos"):
        Settings.from_env()
