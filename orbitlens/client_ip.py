"""Extrae IP solo de proxies explícitamente confiables, desde la derecha."""

import ipaddress


def client_ip(peer: str, forwarded_for: str | None, trusted: tuple[str, ...]) -> str:
    networks = tuple(ipaddress.ip_network(value) for value in trusted)

    def parse(value):
        try:
            return ipaddress.ip_address(value.strip())
        except ValueError:
            return None

    address = parse(peer)
    if address is None:
        return peer  # TestClient/Unix socket; nunca confía en cabeceras.
    if not any(address in network for network in networks) or not forwarded_for:
        return str(address)
    # Una cadena malformada se ignora por completo, no se salta el tramo inválido.
    hops = [parse(value) for value in forwarded_for.split(",")]
    if len(hops) > 32 or any(hop is None for hop in hops):
        return str(address)
    for hop in reversed(hops):
        if not any(address in network for network in networks):
            break
        address = hop
    return str(address)
