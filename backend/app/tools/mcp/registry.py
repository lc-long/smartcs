from __future__ import annotations

import asyncio
import structlog
from typing import Any

logger = structlog.get_logger()


class MCPToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._servers: dict[str, Any] = {}

    def register_tool(self, name: str, description: str, input_schema: dict, server_name: str | None = None) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "server_name": server_name,
        }
        logger.info("mcp_tool_registered", tool=name, server=server_name)

    def register_server(self, name: str, server: Any) -> None:
        self._servers[name] = server
        logger.info("mcp_server_registered", server=name)

    def get_tool(self, name: str) -> dict | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[dict]:
        return list(self._tools.values())

    def find_tool(self, query: str) -> list[dict]:
        results = []
        query_lower = query.lower()
        for tool in self._tools.values():
            if (query_lower in tool["name"].lower() or
                query_lower in tool["description"].lower()):
                results.append(tool)
        return results

    async def call_tool(self, name: str, arguments: dict) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")

        server_name = tool.get("server_name")
        if not server_name:
            raise ValueError(f"Tool {name} has no associated server")

        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"MCP server {server_name} not found")

        return await server.call_tool(name, arguments)

    def clear(self) -> None:
        self._tools.clear()
        self._servers.clear()


_mcp_registry: MCPToolRegistry | None = None


def get_mcp_registry() -> MCPToolRegistry:
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPToolRegistry()
    return _mcp_registry
