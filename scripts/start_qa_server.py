"""Servidor local de QA con datos sintéticos aislados; no usar en producción."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    import uvicorn

    os.chdir(ROOT)
    os.environ["ORBITLENS_DATA_DIR"] = str(ROOT / "data" / "browser-qa")
    os.environ["ORBITLENS_CODE_COMMIT"] = "browser-qa-synthetic"
    demo = runpy.run_path(str(ROOT / "scripts" / "make_demo_result.py"))
    demo["main"]()
    uvicorn.run("api:app", host="127.0.0.1", port=8013, workers=1)


if __name__ == "__main__":
    main()
