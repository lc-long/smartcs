from __future__ import annotations

import asyncio
import random
import structlog
from functools import wraps
from typing import Any, Callable, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


def retry_with_jitter(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 0.5,
    exponential_base: float = 2.0,
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        jitter_range = delay * jitter
                        actual_delay = delay + random.uniform(-jitter_range, jitter_range)

                        logger.warning(
                            "retry_attempt",
                            func=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay=actual_delay,
                            error=str(e),
                        )

                        await asyncio.sleep(actual_delay)
                    else:
                        logger.error(
                            "retry_exhausted",
                            func=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )

            raise last_exception

        return wrapper

    return decorator


def sync_retry_with_jitter(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 0.5,
    exponential_base: float = 2.0,
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        jitter_range = delay * jitter
                        actual_delay = delay + random.uniform(-jitter_range, jitter_range)

                        logger.warning(
                            "retry_attempt_sync",
                            func=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            delay=actual_delay,
                            error=str(e),
                        )

                        import time
                        time.sleep(actual_delay)
                    else:
                        logger.error(
                            "retry_exhausted_sync",
                            func=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )

            raise last_exception

        return wrapper

    return decorator
