from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

import structlog

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


class RateLimiter:
    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._minute_buckets: dict[str, list[float]] = defaultdict(list)
        self._hour_buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        minute_cutoff = now - 60
        hour_cutoff = now - 3600

        with self._lock:
            self._minute_buckets[key] = [
                t for t in self._minute_buckets[key] if t > minute_cutoff
            ]
            self._hour_buckets[key] = [
                t for t in self._hour_buckets[key] if t > hour_cutoff
            ]

            minute_count = len(self._minute_buckets[key])
            hour_count = len(self._hour_buckets[key])

            if minute_count >= self.config.requests_per_minute:
                logger.warning("rate_limit_exceeded", key=key, window="minute")
                return False

            if hour_count >= self.config.requests_per_hour:
                logger.warning("rate_limit_exceeded", key=key, window="hour")
                return False

            self._minute_buckets[key].append(now)
            self._hour_buckets[key].append(now)

            return True

    def get_remaining(self, key: str) -> dict:
        now = time.time()
        minute_cutoff = now - 60
        hour_cutoff = now - 3600

        with self._lock:
            minute_used = len([t for t in self._minute_buckets[key] if t > minute_cutoff])
            hour_used = len([t for t in self._hour_buckets[key] if t > hour_cutoff])

            return {
                "minute_remaining": max(0, self.config.requests_per_minute - minute_used),
                "hour_remaining": max(0, self.config.requests_per_hour - hour_used),
            }


_rate_limiters: dict[str, RateLimiter] = {}


def get_rate_limiter(name: str = "default") -> RateLimiter:
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter()
    return _rate_limiters[name]
