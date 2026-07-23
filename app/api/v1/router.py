from fastapi import APIRouter

from app.api.v1.endpoints import download, health, state

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(download.router)
api_router.include_router(state.router)
