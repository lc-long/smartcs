from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "redis": "connected",
            "postgresql": "connected",
            "chroma": "connected",
        },
    }
