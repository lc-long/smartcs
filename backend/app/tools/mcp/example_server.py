from __future__ import annotations

import asyncio
import structlog
from typing import Annotated, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logger = structlog.get_logger()


def create_example_server() -> Server:
    server = Server("smartcs-example-tools")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_weather",
                description="Get weather information for a city",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                    },
                    "required": ["city"],
                },
            ),
            Tool(
                name="search_web",
                description="Search the web for information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "get_weather":
            city = arguments.get("city", "Unknown")
            return [TextContent(type="text", text=f"Weather in {city}: Sunny, 25°C")]
        elif name == "search_web":
            query = arguments.get("query", "")
            return [TextContent(type="text", text=f"Search results for '{query}': No results found")]
        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


async def main():
    server = create_example_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
