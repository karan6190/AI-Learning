"""
Lesson 3 — your first MCP server.

Remember from Lesson 1: an MCP *server* is a program that OFFERS tools. It doesn't
contain an LLM and it doesn't decide anything — it just says "here are the functions
I can run, call me when you want one."

We build it with FastMCP. FastMCP is a small Python library that turns an ordinary
Python function into an MCP tool with ONE decorator. You write normal functions;
FastMCP handles all the protocol plumbing (the JSON messages, the handshake, etc).

Run this server on its own just to prove it starts:
    python server.py
It will sit there silently, waiting to talk MCP over stdin/stdout. Press Ctrl+C.
Normally you don't run it by hand — a CLIENT launches it (that's Lesson 2's client.py).
"""

# FastMCP ships inside the official `mcp` package. This import is the whole library.
from mcp.server.fastmcp import FastMCP

# 1. Create the server and give it a name. Think of this as "opening the shop".
mcp = FastMCP("my-first-server")


# 2. Register tools. The @mcp.tool() decorator is the ONE line that turns a plain
#    function into something an MCP client can discover and call.
#
#    FastMCP reads three things from the function automatically:
#      * the NAME          -> from the function name  (add, greet)
#      * the INPUT SCHEMA  -> from the type hints      (a: int, b: int)
#      * the DESCRIPTION   -> from the docstring       (the client shows this to the LLM)
#    You don't write any schema by hand — the type hints ARE the schema.

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together and return the result."""
    return a + b


@mcp.tool()
def greet(name: str) -> str:
    """Return a friendly greeting for the given name."""
    return f"Hello, {name}! Nice to meet you."


# 3. Start the server. "stdio" means: talk MCP over standard input/output.
#    This is the simplest transport — the client launches this file as a subprocess
#    and the two exchange JSON messages through that pipe. (Lesson 4 shows HTTP.)
if __name__ == "__main__":
    mcp.run(transport="stdio")
