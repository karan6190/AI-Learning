"""
Lesson 2 — a minimal MCP client (NO LLM yet).

This is the other half from Lesson 1: the CLIENT. Its whole job is to:
  1. launch the server,
  2. DISCOVER what tools the server offers,
  3. CALL a couple of them and print the results.

We deliberately leave the LLM out. Right now YOU are playing the role of the LLM —
you decide which tools to call. In a later lesson an LLM makes that decision instead.
The point here is to see the client/server conversation with nothing else in the way.

Run it:
    python client.py
It will start server.py for you, so you don't run the server yourself.
"""

import asyncio
import os
import sys

# These three come from the official `mcp` SDK (the client side of it).
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# How to launch the server: run server.py with the SAME python that's running us.
# (sys.executable = the current python interpreter; keeps everything consistent.)
SERVER = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(os.path.dirname(__file__), "server.py")],
)


async def main():
    # stdio_client launches the server subprocess and gives us two pipes:
    #   read  = messages coming FROM the server
    #   write = messages going TO the server
    async with stdio_client(SERVER) as (read, write):
        # A ClientSession wraps those pipes and speaks the MCP protocol for us.
        async with ClientSession(read, write) as session:
            # The MCP handshake. Always the first thing a client does.
            await session.initialize()

            # ---- 1. DISCOVERY: ask the server what tools it has ----
            print("=== Tools the server offers ===")
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  • {tool.name}: {tool.description}")

            # ---- 2. CALL a tool: add(2, 3) ----
            print("\n=== Calling add(a=2, b=3) ===")
            result = await session.call_tool("add", {"a": 2, "b": 3})
            # Tool results come back as a list of content blocks; the text is in .text
            print("  server returned:", result.content[0].text)

            # ---- 3. CALL another tool: greet('Ada') ----
            print("\n=== Calling greet(name='Ada') ===")
            result = await session.call_tool("greet", {"name": "Ada"})
            print("  server returned:", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
