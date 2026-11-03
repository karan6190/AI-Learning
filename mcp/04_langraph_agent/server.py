"""
Lesson 4 — the MCP SERVER (unchanged idea from Lessons 2-4).

This is an ordinary FastMCP server. Notice there is NOTHING here about LangGraph,
LLMs, or agents. That's the whole point of MCP: the server just OFFERS tools and
has no idea who will call them. In this lesson the caller happens to be a LangGraph
agent driven by an LLM — but the server code is identical to what a human-driven
client (Lesson 2) or MCP Inspector (Lesson 3) would talk to.

We expose three tiny tools so you can watch the agent pick between them:

  * add(a, b)        -> a + b
  * multiply(a, b)   -> a * b
  * word_count(text) -> number of words in a string

Run it on its own just to prove it starts (it will sit silently, waiting for a
client to talk MCP over the pipe — press Ctrl+C):

    python server.py
"""

from mcp.server.fastmcp import FastMCP

# 1. Create the server ("open the shop"). The name is just a label.
mcp = FastMCP("lesson-5-tools")


# 2. Register tools. One decorator each. FastMCP reads the NAME from the function,
#    the INPUT SCHEMA from the type hints, and the DESCRIPTION from the docstring.
#    The docstring matters a lot now: the LLM reads it to decide WHEN to use a tool.

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together and return the result."""
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together and return the result."""
    return a * b


@mcp.tool()
def word_count(text: str) -> int:
    """Count how many words are in a piece of text."""
    return len(text.split())


# 3. Start the server over stdio (the client launches this file as a subprocess
#    and the two talk through that pipe). Same transport as every earlier lesson.
if __name__ == "__main__":
    mcp.run(transport="stdio")
