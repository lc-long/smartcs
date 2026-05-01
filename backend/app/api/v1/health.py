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


@router.get("/debug/config")
async def debug_config() -> dict:
    settings = get_settings()
    return {
        "llm_provider": settings.llm_provider,
        "default_model": settings.default_model,
        "router_model": settings.router_model,
        "minimax_base_url": settings.minimax_base_url,
    }
