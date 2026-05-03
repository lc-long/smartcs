from __future__ import annotations

import asyncio
import structlog
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.app.tools.mcp.registry import get_mcp_registry

logger = structlog.get_logger()


class MCPClient:
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.session: ClientSession | None = None
        self._tools: list[dict] = []

    async def connect(self, command: str, args: list[str] | None = None, env: dict | None = None) -> None:
        params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
        )

        async with stdio_client(params) as (read, write):
            self.session = ClientSession(read, write)
            await self.session.initialize()

            result = await self.session.list_tools()
            self._tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]

            registry = get_mcp_registry()
            registry.register_server(self.server_name, self)
            for tool in self._tools:
                registry.register_tool(
                    name=tool["name"],
                    description=tool["description"],
                    input_schema=tool["input_schema"],
                    server_name=self.server_name,
                )

            logger.info("mcp_client_connected", server=self.server_name, tool_count=len(self._tools))

    async def call_tool(self, name: str, arguments: dict) -> Any:
        if not self.session:
            raise RuntimeError("MCP client not connected")

        result = await self.session.call_tool(name, arguments)
        return result.content

    async def disconnect(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("mcp_client_disconnected", server=self.server_name)


_mcp_clients: dict[str, MCPClient] = {}


async def connect_mcp_server(
    server_name: str,
    command: str,
    args: list[str] | None = None,
    env: dict | None = None,
) -> MCPClient:
    client = MCPClient(server_name)
    await client.connect(command, args, env)
    _mcp_clients[server_name] = client
    return client


async def disconnect_mcp_server(server_name: str) -> None:
    client = _mcp_clients.pop(server_name, None)
    if client:
        await client.disconnect()


def get_mcp_client(server_name: str) -> MCPClient | None:
    return _mcp_clients.get(server_name)
