from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerStats:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = field(default_factory=time.time)


class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._stats.state

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self._stats.state == CircuitState.OPEN:
                if time.time() - self._stats.last_failure_time >= self.config.timeout_seconds:
                    logger.info("circuit_breaker_half_open", name=self.name)
                    self._stats.state = CircuitState.HALF_OPEN
                    self._stats.consecutive_failures = 0
                    self._stats.consecutive_successes = 0
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")

            self._stats.total_calls += 1

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            self._stats.successful_calls += 1
            self._stats.consecutive_successes += 1
            self._stats.consecutive_failures = 0

            if self._stats.state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.config.success_threshold:
                    logger.info("circuit_breaker_closed", name=self.name)
                    self._stats.state = CircuitState.CLOSED
                    self._stats.consecutive_successes = 0

    async def _on_failure(self) -> None:
        async with self._lock:
            self._stats.failed_calls += 1
            self._stats.consecutive_failures += 1
            self._stats.consecutive_successes = 0
            self._stats.last_failure_time = time.time()

            if self._stats.state == CircuitState.HALF_OPEN:
                logger.warning("circuit_breaker_reopened", name=self.name)
                self._stats.state = CircuitState.OPEN
            elif self._stats.consecutive_failures >= self.config.failure_threshold:
                logger.warning("circuit_breaker_opened", name=self.name)
                self._stats.state = CircuitState.OPEN

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "state": self._stats.state.value,
            "total_calls": self._stats.total_calls,
            "successful_calls": self._stats.successful_calls,
            "failed_calls": self._stats.failed_calls,
            "consecutive_failures": self._stats.consecutive_failures,
        }


class CircuitBreakerOpenError(Exception):
    pass


_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]
