import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.cors import setup_cors
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_path, debug=settings.debug)
    logger = logging.getLogger("app.main")
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    for dir_path in [settings.log_path, settings.download_path]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory: %s", dir_path)

    logger.info("Startup complete")
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Service for downloading a text-file catalog from an external API with statistics.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    setup_cors(app)
    register_exception_handlers(app)
    app.include_router(api_router)

    frontend_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        if not frontend_path.exists():
            raise HTTPException(status_code=404, detail="Frontend not found")
        return FileResponse(path=frontend_path, media_type="text/html")

    return app


app = create_app()
