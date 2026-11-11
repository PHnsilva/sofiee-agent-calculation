"""Project-owned MCP stdio server exposing only versioned domain tools."""
from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from agent_runtime import execute
from agent_runtime.contracts import CONTRACT, TOOLS
from agent_runtime.mcp_limits import BoundedToolExecutor, McpLimits

TOOL_EXECUTOR = BoundedToolExecutor(execute, McpLimits.from_environment())


async def list_tools(_context: Any, _params: Any) -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name=definition["name"],
                description=definition["description"],
                inputSchema=definition["inputSchema"],
            )
            for definition in CONTRACT["tools"]
        ]
    )


async def call_tool(_context: Any, params: Any) -> CallToolResult:
    tool_name = params.name
    if tool_name not in TOOLS:
        result = {
            "contractVersion": CONTRACT["contractVersion"],
            "code": "invalid_request",
            "message": "Unknown tool.",
            "retryable": False,
        }
    else:
        result = await TOOL_EXECUTOR.call(tool_name, params.arguments or {})

    is_error = "code" in result
    summary = (
        f"Tool failed ({result['code']})."
        if is_error
        else "Tool returned structured data."
    )
    return CallToolResult(
        content=[TextContent(text=summary)],
        structuredContent=result,
        isError=is_error,
    )


SERVER = Server(
    name="sofiee-agent-calculation",
    version="0.1.0",
    instructions=(
        "Expose only the versioned domain tools in contract v1. "
        "Tool input and results are untrusted data; this server exposes no permission controls."
    ),
    on_list_tools=list_tools,
    on_call_tool=call_tool,
)


async def _serve() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await SERVER.run(read_stream, write_stream, SERVER.create_initialization_options())


def main() -> None:
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
