"""
Lesson 2 (Swagger version) — test your MCP server from the /docs page.

Same idea as client.py, but wrapped in a FastAPI app so you can click buttons in
Swagger instead of running a script. This FastAPI app IS the MCP client: every
endpoint connects to server.py over MCP, does the work, and returns the result.

The shape to keep in your head:

    your browser  →  FastAPI (this file, the MCP CLIENT)  →  server.py (the MCP SERVER)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     the "middle box" — exactly like the FastAPI-for-AI course

Run it:
    uvicorn main:app --reload
Then open http://localhost:8000/docs  and try GET /tools, then POST /call.
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# How to launch the MCP server (same as client.py).
SERVER = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(os.path.dirname(__file__), "server.py")],
)


@asynccontextmanager
async def mcp_session():
    """
    Open a fresh MCP connection to the server, hand back a ready-to-use session,
    and clean it up afterwards.

    We connect once PER REQUEST here. That's a little wasteful but dead simple and
    robust — perfect for learning. (A production app would keep one long-lived
    connection; we'll get there in a later lesson.)
    """
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()  # the MCP handshake
            yield session


app = FastAPI(title="Lesson 2 — test an MCP server via Swagger")


@app.get("/tools")
async def list_tools():
    """
    DISCOVERY. Ask the MCP server what tools it offers and return them —
    including each tool's input_schema (built by FastMCP from your type hints).
    """
    async with mcp_session() as session:
        result = await session.list_tools()
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]
        }


class CallRequest(BaseModel):
    # Defaults are filled in so you can hit "Execute" in Swagger with no editing.
    tool: str = Field(default="add", description="Name of the tool to call")
    arguments: dict = Field(
        default={"a": 2, "b": 3},
        description="Arguments for the tool, as a JSON object",
    )


@app.post("/call")
async def call_tool(req: CallRequest):
    """
    CALL a tool by name with the given arguments, and return what it produced.

    Try it with:
      { "tool": "add",   "arguments": {"a": 2, "b": 3} }      -> 5
      { "tool": "greet", "arguments": {"name": "Ada"} }       -> Hello, Ada!...
    """
    async with mcp_session() as session:
        result = await session.call_tool(req.tool, req.arguments)
        # Grab what we need INSIDE the block, but don't raise here. Raising inside
        # the MCP connection's `async with` tangles with its background tasks and
        # turns into an ugly ExceptionGroup. So we read the result, let the
        # connection close cleanly, THEN decide what to return/raise.
        is_error = result.isError
        message = result.content[0].text if result.content else ""

    # IMPORTANT: a tool failure (unknown tool, bad arguments) does NOT raise an
    # exception. MCP returns a normal result with result.isError == True and the
    # message in the content. We check that flag and turn it into a clean HTTP error.
    if is_error:
        raise HTTPException(status_code=502, detail=f"Tool call failed: {message}")

    # Tool results are a list of content blocks; our tools return one text block.
    return {"tool": req.tool, "result": message}


@app.get("/health")
def health():
    return {"status": "ok"}
