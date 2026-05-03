from __future__ import annotations

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.services.rate_limiter import get_rate_limiter

import structlog

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"

        limiter = get_rate_limiter("global")

        if not limiter.is_allowed(key):
            raise HTTPException(status_code=429, detail="Too many requests")

        response = await call_next(request)
        remaining = limiter.get_remaining(key)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining["minute_remaining"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining["hour_remaining"])
        return response
