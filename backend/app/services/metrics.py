from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

import structlog

logger = structlog.get_logger()


@dataclass
class MetricPoint:
    timestamp: float
    value: float
    labels: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    def __init__(self, retention_minutes: int = 60):
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timers: dict[str, float] = {}
        self._lock = Lock()
        self._retention = retention_minutes * 60
        self._start_time = time.time()

    def increment(self, name: str, value: float = 1.0, labels: dict | None = None) -> None:
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def histogram(self, name: str, value: float, labels: dict | None = None) -> None:
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            self._cleanup_histogram(key)

    def timer_start(self, name: str) -> None:
        self._timers[name] = time.time()

    def timer_end(self, name: str) -> float | None:
        start = self._timers.pop(name, None)
        if start:
            elapsed = time.time() - start
            self.histogram(f"{name}.duration", elapsed)
            return elapsed
        return None

    def _make_key(self, name: str, labels: dict | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _cleanup_histogram(self, key: str) -> None:
        cutoff = time.time() - self._retention
        self._histograms[key] = [
            v for v in self._histograms[key] if v > cutoff
        ]

    def get_stats(self) -> dict:
        with self._lock:
            uptime = time.time() - self._start_time

            histogram_stats = {}
            for key, values in self._histograms.items():
                if values:
                    sorted_vals = sorted(values)
                    histogram_stats[key] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": sorted_vals[len(sorted_vals) // 2],
                        "p95": sorted_vals[int(len(sorted_vals) * 0.95)],
                        "p99": sorted_vals[int(len(sorted_vals) * 0.99)],
                    }

            return {
                "uptime_seconds": uptime,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histogram_stats,
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()


_metrics: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
