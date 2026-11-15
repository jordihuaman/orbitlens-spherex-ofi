"""Arranque de producción: un proceso, proxy headers resueltos en la aplicación."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitlens.config import Settings  # noqa: E402

if __name__ == "__main__":
    settings = Settings.from_env()
    # Escucha en todas las interfaces dentro del contenedor; el puerto solo se
    # publica en 127.0.0.1 vía compose y el proxy/TLS termina fuera.
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")),  # nosec B104
                workers=1, proxy_headers=False, server_header=False, access_log=False,
                timeout_graceful_shutdown=int(settings.job_timeout_s + 30))
