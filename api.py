"""Aplicación FastAPI de OrbitLens.

Ejecutar en desarrollo:
    .\\.venv\\Scripts\\python.exe -m uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from orbitlens import __version__
from orbitlens.api_models import SearchRequest
from orbitlens.client_ip import client_ip
from orbitlens.config import PIPELINE_VERSION, Settings
from orbitlens.jobs import JobCapacityError, JobManager
from orbitlens.manifest import validate_file_entry, validate_manifest, validate_result_files
from orbitlens.service import SearchService
from orbitlens.targets import public_presets

RESULT_ID_RE = re.compile(r"^[a-f0-9]{16}$")
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend" / "dist"


def create_app(
    *,
    settings: Settings | None = None,
    service: SearchService | None = None,
    manager: JobManager | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_settings = settings or Settings.from_env()
        owned_service = service is None
        owned_manager = manager is None
        active_service = service or SearchService(active_settings)
        active_manager = manager or JobManager(
            max_workers=active_settings.max_workers,
            max_active=active_settings.max_active_jobs,
            max_active_per_ip=active_settings.max_active_per_ip,
            searches_per_minute=active_settings.searches_per_minute,
            store_dir=active_settings.data_dir / "jobs",
        )
        app.state.settings = active_settings
        app.state.service = active_service
        app.state.manager = active_manager
        try:
            yield
        finally:
            if owned_manager:
                active_manager.shutdown(wait=True)
            if owned_service:
                active_service.close()

    app = FastAPI(
        title="OrbitLens SPHEREx",
        version=__version__,
        description="Secuencias temporales de imágenes SPHEREx a partir de RA/Dec.",
        lifespan=lifespan,
    )

    active_settings = settings or Settings.from_env()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def get_settings(request: Request) -> Settings:
        return request.app.state.settings

    def get_manager(request: Request) -> JobManager:
        return request.app.state.manager

    def get_service(request: Request) -> SearchService:
        return request.app.state.service

    @app.get("/api/health")
    def health(request: Request) -> dict[str, object]:
        current = get_settings(request)
        return {
            "status": "ok",
            "version": __version__,
            "pipeline_version": PIPELINE_VERSION,
            "code_commit": os.environ.get("ORBITLENS_CODE_COMMIT", "dev"),
            "collections": list(current.collections),
            "active_jobs": get_manager(request).active_count,
        }

    @app.get("/api/presets")
    def presets(request: Request) -> dict[str, object]:
        items = public_presets()
        index_path = get_settings(request).data_dir / "presets.json"
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            index = {}
        if not isinstance(index, dict):
            index = {}
        for item in items:
            result_id = index.get(item["id"])
            if not isinstance(result_id, str) or not RESULT_ID_RE.fullmatch(result_id):
                continue
            root = get_settings(request).data_dir / "results" / result_id
            try:
                manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
                validate_result_files(root, manifest)
                if any(frame.get("collection") == "synthetic-demo" for frame in manifest["frames"]):
                    continue
                if (manifest["result_id"] != result_id
                        or abs(manifest["request"]["ra_deg"] - item["ra_deg"]) > 1e-7
                        or abs(manifest["request"]["dec_deg"] - item["dec_deg"]) > 1e-7):
                    continue
                item.update(result_id=result_id, result_status=manifest.get("status", "partial"),
                            result_method=manifest["search"].get("method", "sia"),
                            manifest_url=f"/api/results/{result_id}/manifest")
            except (OSError, ValueError, TypeError, KeyError):
                continue
        return {"presets": items, "count": len(items)}

    @app.post("/api/search", status_code=202)
    def start_search(payload: SearchRequest, request: Request) -> JSONResponse:
        normalized = payload.normalized()
        key = json.dumps(normalized, sort_keys=True)
        current_service = get_service(request)
        try:
            job, created = get_manager(request).submit(
                normalized, key, lambda current_job: current_service.run(current_job, normalized),
                owner=client_ip(request.client.host if request.client else "unknown",
                                request.headers.get("x-forwarded-for"), get_settings(request).trusted_proxies),
            )
        except JobCapacityError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": str(getattr(exc, "retry_after", 30))},
            ) from exc

        return JSONResponse(
            status_code=202,
            content={
                "job_id": job.id,
                "status": job.status,
                "status_url": f"/api/status/{job.id}",
                "deduplicated": not created,
            },
        )

    @app.get("/api/status/{job_id}")
    def job_status(job_id: str, request: Request) -> dict[str, object]:
        job = get_manager(request).get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="trabajo desconocido")
        return job.public()

    def load_manifest(request: Request, result_id: str) -> tuple[Path, dict]:
        if not RESULT_ID_RE.fullmatch(result_id):
            raise HTTPException(status_code=404, detail="resultado desconocido")
        result_dir = get_settings(request).data_dir / "results" / result_id
        manifest_path = result_dir / "manifest.json"
        if not manifest_path.is_file():
            raise HTTPException(status_code=404, detail="resultado desconocido")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_manifest(manifest)
            if manifest["result_id"] != result_id:
                raise ValueError("ID del manifiesto no coincide con su directorio")
        except (OSError, ValueError, TypeError) as exc:
            raise HTTPException(status_code=500, detail="manifiesto ilegible") from exc
        return result_dir, manifest

    @app.get("/api/results/{result_id}/manifest")
    def result_manifest(result_id: str, request: Request) -> JSONResponse:
        result_dir, manifest = load_manifest(request, result_id)
        try:
            validate_result_files(result_dir, manifest)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="resultado incompleto o corrupto") from exc
        return JSONResponse(content=manifest)

    @app.get("/api/results/{result_id}/files/{file_id}")
    def result_file(result_id: str, file_id: str, request: Request) -> FileResponse:
        result_dir, manifest = load_manifest(request, result_id)
        entry = next(
            (item for item in manifest.get("files", []) if isinstance(item, dict) and item.get("id") == file_id),
            None,
        )
        if entry is None:
            raise HTTPException(status_code=404, detail="archivo no indexado")

        relative = Path(str(entry.get("path", "")))
        candidate = (result_dir / relative).resolve()
        if not candidate.is_relative_to(result_dir.resolve()) or not candidate.is_file():
            raise HTTPException(status_code=404, detail="archivo no disponible")

        try:
            validate_file_entry(result_dir, entry)
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="integridad del archivo inválida") from exc

        media_type = "image/png" if entry.get("kind") == "png" else "application/fits"
        return FileResponse(candidate, media_type=media_type)

    @app.get("/", response_model=None)
    def index() -> FileResponse | dict[str, str]:
        index_file = FRONTEND_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return {
            "message": "OrbitLens API",
            "health": "/api/health",
            "docs": "/docs",
        }

    if FRONTEND_DIR.is_dir():
        assets_dir = FRONTEND_DIR / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str) -> FileResponse:
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="ruta desconocida")
            candidate = (FRONTEND_DIR / full_path).resolve()
            if (
                candidate.is_relative_to(FRONTEND_DIR.resolve())
                and candidate.is_file()
            ):
                return FileResponse(candidate)
            return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
