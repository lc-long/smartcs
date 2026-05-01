from __future__ import annotations

import time
from typing import Any

import structlog
from langchain_core.tools import BaseTool, tool

logger = structlog.get_logger()


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool_instance: BaseTool) -> None:
        self._tools[tool_instance.name] = tool_instance
        logger.info("tool_registered", tool_name=tool_instance.name)

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_by_names(self, names: list[str]) -> list[BaseTool]:
        return [self._tools[n] for n in names if n in self._tools]


_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def timed_tool(func: Any) -> Any:
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed_ms = int((time.time() - start) * 1000)
        logger.info(
            "tool_executed",
            tool_name=func.__name__,
            latency_ms=elapsed_ms,
        )
        return result
    return wrapper
