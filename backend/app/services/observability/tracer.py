from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator
from uuid import uuid4

import structlog

logger = structlog.get_logger()


class TraceContext:
    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or uuid4().hex
        self.spans: list[dict[str, Any]] = []
        self._start_time = time.time()

    def add_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        duration_ms: int | None = None,
    ) -> None:
        span = {
            "trace_id": self.trace_id,
            "span_name": name,
            "timestamp": time.time(),
            "duration_ms": duration_ms,
            "attributes": attributes or {},
        }
        self.spans.append(span)
        logger.info("trace_span", **span)

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Generator[None, None, None]:
        start = time.time()
        try:
            yield
        finally:
            elapsed_ms = int((time.time() - start) * 1000)
            self.add_span(name, attributes=attributes, duration_ms=elapsed_ms)

    def get_summary(self) -> dict[str, Any]:
        total_ms = int((time.time() - self._start_time) * 1000)
        return {
            "trace_id": self.trace_id,
            "total_duration_ms": total_ms,
            "span_count": len(self.spans),
            "spans": self.spans,
        }


_traces: dict[str, TraceContext] = {}


def get_or_create_trace(trace_id: str | None = None) -> TraceContext:
    if trace_id and trace_id in _traces:
        return _traces[trace_id]
    ctx = TraceContext(trace_id)
    _traces[ctx.trace_id] = ctx
    return ctx


def get_trace(trace_id: str) -> TraceContext | None:
    return _traces.get(trace_id)
