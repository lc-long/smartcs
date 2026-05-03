from fastapi import APIRouter, Response
from pydantic import BaseModel

from backend.app.services.metrics import get_metrics

router = APIRouter(prefix="/api/v1", tags=["metrics"])


class MetricsResponse(BaseModel):
    uptime_seconds: float
    counters: dict
    gauges: dict
    histograms: dict


@router.get("/metrics")
async def get_metrics_endpoint() -> MetricsResponse:
    metrics = get_metrics()
    return metrics.get_stats()
