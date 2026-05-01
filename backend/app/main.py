from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.traces import router as traces_router
from backend.app.api.websocket.chat_ws import handle_websocket
from backend.app.core.config.settings import get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from backend.app.core.database import close_db, init_db
    from backend.app.services.redis.client import close_redis

    settings = get_settings()
    logger.info(
        "app_startup",
        app_name=settings.app_name,
        env=settings.app_env.value,
        debug=settings.debug,
    )

    await init_db()
    logger.info("database_initialized")

    yield

    await close_redis()
    await close_db()
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Enterprise Multi-Agent Customer Service System",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(health_router)
    app.include_router(traces_router)
    app.include_router(admin_router)

    @app.websocket("/ws/chat/{conversation_id}")
    async def websocket_chat(websocket: WebSocket, conversation_id: str) -> None:
        customer_id = websocket.query_params.get("customer_id", "anonymous")
        await handle_websocket(websocket, conversation_id, customer_id)

    return app


app = create_app()
