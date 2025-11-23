#!/usr/bin/env python3
"""
Simple MCP client test to see what tools our server is exposing
"""

import asyncio
import json
import subprocess
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client


async def test_mcp_tools():
    """Test what tools our MCP server is exposing"""

    # Server command to test - need to start subprocess
    server_process = subprocess.Popen(
        ["uv", "run", "python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        async with stdio_client(server_cmd) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()

                # List available tools
                tools = await session.list_tools()

                print("=== Available Tools ===")
                for tool in tools.tools:
                    print(f"Name: {tool.name}")
                    print(f"Description: {tool.description}")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        print(f"Schema: {json.dumps(tool.inputSchema, indent=2)}")
                    print("---")

                return tools

    except Exception as e:
        print(f"Error testing MCP server: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())