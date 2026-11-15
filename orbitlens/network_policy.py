"""Política de salida: HTTPS, hosts exactos y sin redirects implícitos."""

from urllib.parse import urlsplit


def validate_remote_url(url: str, allowed_hosts: tuple[str, ...]) -> None:
    try:
        parts = urlsplit(url)
        valid = (parts.scheme == "https" and parts.hostname in allowed_hosts
                 and not parts.username and not parts.password and parts.port in (None, 443)
                 and not parts.fragment and not any(ord(char) < 33 for char in url))
    except ValueError:
        valid = False
    if not valid:
        # No reproducir una URL que podría incluir credenciales/control characters.
        raise ValueError("URL remota rechazada por la política HTTPS/host/puerto")
