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
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")),
                workers=1, proxy_headers=False,
                timeout_graceful_shutdown=int(settings.job_timeout_s + 30))
