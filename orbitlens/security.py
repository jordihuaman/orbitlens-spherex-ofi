"""Controles HTTP ASGI, antes del parseo de JSON y de trabajo costoso."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import logging
import math
import threading
import time
import uuid
from collections import OrderedDict
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

from .client_ip import client_ip
from .config import Settings

logger = logging.getLogger("orbitlens.security")


def security_headers(settings: Settings) -> dict[str, str]:
    headers = {
        "Content-Security-Policy": (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
            "font-src 'self'; connect-src 'self'; media-src 'none'; object-src 'none'; "
            "frame-src 'none'; worker-src 'self'; manifest-src 'self'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
            "accelerometer=(), gyroscope=(), magnetometer=(), serial=(), xr-spatial-tracking=()"
        ),
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "X-Permitted-Cross-Domain-Policies": "none",
    }
    if settings.production:
        headers["Strict-Transport-Security"] = "max-age=31536000"
    return headers


def cache_control_for(path: str) -> str:
    """Los activos con hash de Vite son inmutables; el resto se revalida."""
    if path.startswith("/api/"):
        return "no-store"
    if path.startswith("/assets/"):
        return "public, max-age=31536000, immutable"
    return "no-cache"


class RequestLimiter:
    """Token bucket por IP, sin IPs persistidas y con cardinalidad acotada."""

    def __init__(self, per_minute: int, burst: int, max_clients: int, clock=time.monotonic):
        self.rate, self.burst, self.max_clients = per_minute / 60, burst, max_clients
        self.clock = clock
        self._clients = OrderedDict()
        self._lock = threading.Lock()

    def admit(self, address: str) -> int | None:
        key = hashlib.sha256(address.encode()).hexdigest()
        with self._lock:
            now = self.clock()
            while self._clients and next(iter(self._clients.values()))[1] < now - 120:
                self._clients.popitem(last=False)
            if key not in self._clients and len(self._clients) >= self.max_clients:
                return 30
            tokens, previous = self._clients.pop(key, (self.burst, now))
            tokens = min(self.burst, tokens + max(0, now - previous) * self.rate)
            retry = max(1, math.ceil((1 - tokens) / self.rate)) if tokens < 1 else None
            self._clients[key] = (tokens if retry else tokens - 1, now)
            return retry


def _trusted_peer(peer: str, networks: tuple[str, ...]) -> bool:
    try:
        address = ipaddress.ip_address(peer)
        return any(address in ipaddress.ip_network(network) for network in networks)
    except ValueError:
        return False


class SecurityMiddleware:
    def __init__(self, app, settings: Settings):
        self.app, self.settings = app, settings
        self.limiter = RequestLimiter(settings.http_requests_per_minute, settings.http_burst, settings.max_http_clients)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started, status = time.monotonic(), 500
        headers = {}
        for key, value in scope.get("headers", []):
            headers.setdefault(key.lower(), []).append(value.decode("latin-1"))

        async def secured_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                added = security_headers(self.settings)
                added["X-Request-ID"] = request_id
                added["Cache-Control"] = cache_control_for(scope["path"]) if status < 400 else "no-store"
                existing = [(key, value) for key, value in message.get("headers", [])
                            if key.lower().decode() not in {name.lower() for name in added}]
                message = {**message, "headers": [*existing, *((k.lower().encode(), v.encode()) for k, v in added.items())]}
            await send(message)

        async def reject(code, detail, extra=None):
            log = logger.warning if code >= 500 else logger.info
            log(json.dumps({"event": "http_rejected", "request_id": request_id, "status": code}))
            await JSONResponse({"detail": detail, "request_id": request_id}, status_code=code,
                               headers={"Cache-Control": "no-store", **(extra or {})})(scope, receive, secured_send)

        peer = (scope.get("client") or ("unknown", 0))[0]
        forwarded = ",".join(headers.get(b"x-forwarded-for", [])) or None
        address = client_ip(peer, forwarded, self.settings.trusted_proxies)
        if retry := self.limiter.admit(address):
            return await reject(429, "demasiadas solicitudes; vuelva a intentarlo", {"Retry-After": str(retry)})

        host_values = headers.get(b"host", [])
        if len(host_values) != 1:
            return await reject(400, "cabecera Host inválida")
        host = host_values[0]
        try:
            parts = urlsplit("http://" + host)
            if (parts.username or parts.password or parts.path or parts.query or parts.fragment
                    or not parts.hostname or parts.port == 0 or any(c.isspace() for c in host)):
                raise ValueError("host")
            allowed = {value.strip("[]").lower() for value in self.settings.allowed_hosts}
            if parts.hostname.lower() not in allowed:
                return await reject(400, "host no permitido")
        except ValueError:
            return await reject(400, "cabecera Host inválida")
        if len(scope["path"]) + len(scope.get("query_string", b"")) > 4096:
            return await reject(414, "URL demasiado larga")
        if not self.settings.enable_docs and scope["path"] in {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}:
            return await reject(404, "ruta desconocida")
        # Solo el proxy autorizado puede afirmar que el cliente usó TLS.
        secure = scope.get("scheme") == "https" or (
            _trusted_peer(peer, self.settings.trusted_proxies)
            and headers.get(b"x-forwarded-proto") == ["https"])
        if self.settings.production and not secure and scope["path"] != "/api/health":
            return await reject(426, "se requiere HTTPS")

        if scope["method"] in {"POST", "PUT", "PATCH", "DELETE"}:
            origins = headers.get(b"origin", [])
            allowed_origins = {*(self.settings.cors_origins), self.settings.public_origin}
            if not self.settings.production:
                allowed_origins.add(f"{scope.get('scheme', 'http')}://{host}")
            if ((origins and (len(origins) != 1 or origins[0] not in allowed_origins))
                    or (headers.get(b"sec-fetch-site") == ["cross-site"] and not origins)):
                return await reject(403, "origen de solicitud no permitido")
            if headers.get(b"content-encoding", ["identity"]) != ["identity"]:
                return await reject(415, "Content-Encoding no soportado")
            content_type = headers.get(b"content-type", [""])
            if len(content_type) != 1 or content_type[0].split(";")[0].strip().lower() != "application/json":
                return await reject(415, "se requiere application/json")
            lengths = headers.get(b"content-length", [])
            transfer = headers.get(b"transfer-encoding", [])
            if (len(lengths) > 1 or len(transfer) > 1
                    or (lengths and transfer)
                    or (transfer and [value.lower() for value in transfer] != ["chunked"])):
                return await reject(400, "delimitación del cuerpo inválida")
            try:
                if lengths and not lengths[0].isdigit():
                    raise ValueError("length")
                if lengths and int(lengths[0]) > self.settings.max_request_bytes:
                    return await reject(413, "cuerpo de solicitud demasiado grande")
            except ValueError:
                return await reject(400, "Content-Length inválido")
            body = bytearray()
            deadline = time.monotonic() + self.settings.request_body_timeout_s
            try:
                while True:
                    message = await asyncio.wait_for(receive(), timeout=max(0.001, deadline - time.monotonic()))
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > self.settings.max_request_bytes:
                        return await reject(413, "cuerpo de solicitud demasiado grande")
                    if not message.get("more_body", False):
                        break
            except TimeoutError:
                return await reject(408, "tiempo de recepción agotado")
            if lengths and len(body) != int(lengths[0]):
                return await reject(400, "longitud del cuerpo no coincide")
            original_receive = receive
            delivered = False

            async def replay_receive():
                nonlocal delivered
                if delivered:
                    return await original_receive()
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            receive = replay_receive
        try:
            await self.app(scope, receive, secured_send)
        finally:
            # Sin IP, query ni cabeceras: solo lo necesario para operar y depurar.
            logger.info(json.dumps({"event": "http", "request_id": request_id,
                                    "method": scope.get("method", "")[:12],
                                    "path": scope.get("path", "")[:200],
                                    "status": status,
                                    "duration_ms": round((time.monotonic() - started) * 1000)}))
