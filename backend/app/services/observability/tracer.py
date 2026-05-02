from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator
from uuid import uuid4

import structlog

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

logger = structlog.get_logger()


class InMemoryTracer:
    """Fallback in-memory tracer when OpenTelemetry is not available."""

    def __init__(self):
        self._traces: dict[str, "TraceContext"] = {}

    def get_or_create_trace(self, trace_id: str | None = None) -> "TraceContext":
        if trace_id and trace_id in self._traces:
            return self._traces[trace_id]
        ctx = TraceContext(trace_id)
        self._traces[ctx.trace_id] = ctx
        return ctx

    def get_trace(self, trace_id: str) -> "TraceContext | None":
        return self._traces.get(trace_id)

    def list_traces(self) -> list[str]:
        return list(self._traces.keys())


class TraceContext:
    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or uuid4().hex
        self.spans: list[dict[str, Any]] = []
        self._start_time = time.time()
        self._current_span = None

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


class OpenTelemetryTracer:
    """OpenTelemetry-based tracer for production use."""

    def __init__(self):
        if not OTEL_AVAILABLE:
            raise RuntimeError("OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk")

        self._provider = TracerProvider()
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        self._provider.add_span_processor(processor)
        trace.set_tracer_provider(self._provider)
        self._tracer = trace.get_tracer(__name__)

    def get_or_create_trace(self, trace_id: str | None = None) -> "OTelTraceContext":
        return OTelTraceContext(self._tracer, trace_id)

    def get_trace(self, trace_id: str) -> "OTelTraceContext | None":
        return None


class OTelTraceContext:
    """OpenTelemetry trace context wrapper."""

    def __init__(self, tracer, trace_id: str | None = None):
        self._tracer = tracer
        self._span = tracer.start_span(trace_id or uuid4().hex)

    def add_span(self, name: str, attributes: dict[str, Any] | None = None, duration_ms: int | None = None):
        with self._tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v) if v is not None else "")
            if duration_ms:
                span.set_attribute("duration_ms", duration_ms)

    @contextmanager
    def span(self, name: str, **attributes: Any):
        with self._tracer.start_as_current_span(name) as span:
            try:
                yield
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                pass

    def get_summary(self) -> dict[str, Any]:
        return {"trace_id": self._span.context.trace_id if hasattr(self._span, "context") else "unknown"}


_tracer_impl: InMemoryTracer | OpenTelemetryTracer | None = None


def get_tracer() -> InMemoryTracer | OpenTelemetryTracer:
    global _tracer_impl
    if _tracer_impl is None:
        if OTEL_AVAILABLE:
            try:
                _tracer_impl = OpenTelemetryTracer()
                logger.info("using_opentelemetry_tracer")
            except Exception as e:
                logger.warning("opentelemetry_init_failed", error=str(e))
                _tracer_impl = InMemoryTracer()
                logger.info("using_inmemory_tracer")
        else:
            _tracer_impl = InMemoryTracer()
            logger.info("using_inmemory_tracer")
    return _tracer_impl


def get_or_create_trace(trace_id: str | None = None) -> TraceContext:
    tracer = get_tracer()
    if isinstance(tracer, InMemoryTracer):
        return tracer.get_or_create_trace(trace_id)
    return tracer.get_or_create_trace(trace_id)


def get_trace(trace_id: str) -> TraceContext | None:
    tracer = get_tracer()
    if isinstance(tracer, InMemoryTracer):
        return tracer.get_trace(trace_id)
    return tracer.get_trace(trace_id)


def get_all_trace_ids() -> list[str]:
    tracer = get_tracer()
    if isinstance(tracer, InMemoryTracer):
        return tracer.list_traces()
    return []