from __future__ import annotations

import structlog
from fastapi import APIRouter

from backend.app.services.observability.tracer import get_trace

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["observability"])


@router.get("/traces/{trace_id}")
async def get_trace_detail(trace_id: str) -> dict:
    trace = get_trace(trace_id)
    if trace is None:
        return {"error": "Trace not found", "trace_id": trace_id}
    return trace.get_summary()
