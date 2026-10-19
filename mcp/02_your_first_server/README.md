# Lesson 2 — your first MCP server (with FastMCP)

**Goal:** build the smallest real MCP **server**, then watch a **client** discover and call its
tools. No LLM yet — you'll play the LLM's role by hand, so you can see the client/server
conversation with nothing else in the way.

> Recap from Lesson 1: a **server** *offers* tools; a **client** *uses* them. They're separate
> programs that talk over the MCP protocol. This lesson is one of each.

---

## What is FastMCP? (from the basics)

Writing an MCP server *by hand* means dealing with the raw protocol: JSON messages, a
handshake, listening on a pipe, replying in exactly the right format. Tedious and easy to get
wrong.

**FastMCP is a small Python library that hides all of that.** You write a normal Python
function, add one decorator, and FastMCP turns it into a proper MCP tool. It's the server-side
toolkit — think of it as *"FastAPI, but for MCP tools"* (same idea: decorate a function, done).

It lives inside the official `mcp` package, so:

```python
from mcp.server.fastmcp import FastMCP
```

### The three things FastMCP does for you — automatically

When you decorate a function with `@mcp.tool()`, FastMCP builds the tool's definition by
*reading your function*:

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together and return the result."""
    return a + b
```

| What the client sees | Where FastMCP got it |
|----------------------|----------------------|
| tool **name** = `add` | the function name |
| **inputs** = `a` (int), `b` (int) | the **type hints** — the hints *are* the schema |
| **description** = "Add two numbers…" | the **docstring** |

You never write a schema by hand. This is why type hints and a docstring aren't optional
niceties here — they're how the tool describes itself to the outside world.

---

## The files in this lesson

- `server.py` — the MCP **server** (offers the tools). You never change this to test.
- `main.py` — a **FastAPI app that is the MCP client**. Gives you a Swagger `/docs` page to
  click through. **This is the easy way to test.**
- `client.py` — the same client as a plain **script** (no FastAPI), if you'd rather see the
  bare conversation in a terminal.

---

## Easiest way to test: Swagger (`main.py`)

Just like the FastAPI-for-AI course, we wrap the MCP client in a FastAPI app so you can test
tools by clicking buttons instead of running scripts.

```
   your browser  →  FastAPI (main.py = the MCP CLIENT)  →  server.py (the MCP SERVER)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     the "middle box"
```

Run it:

```bash
cd mcp/lessons/02_your_first_server
pip install "mcp>=1.2" "fastapi>=0.110" "uvicorn[standard]>=0.29"
uvicorn main:app --reload
```

Open **<http://localhost:8000/docs>** and you get three endpoints to play with:

| Endpoint | What it does |
|----------|--------------|
| `GET /tools` | **Discovery** — lists every tool the server offers, *with its input schema* (built by FastMCP from your type hints) |
| `POST /call` | **Call a tool** — pass a `tool` name and an `arguments` object, get the result |
| `GET /health` | is the app up |

**Try this in Swagger:**

1. `GET /tools` → **Try it out → Execute**. You'll see `add` and `greet`, each with the exact
   arguments it expects. Nobody typed that in — the app *discovered* it from the server.
2. `POST /call` → **Try it out**. The box is pre-filled with
   `{ "tool": "add", "arguments": {"a": 2, "b": 3} }` → **Execute** → result `5`.
3. Change the body to `{ "tool": "greet", "arguments": {"name": "Ada"} }` → **Execute** →
   `Hello, Ada! Nice to meet you.`
4. Now break it on purpose: `{ "tool": "nope", "arguments": {} }` → you get a **502** with
   `Tool call failed: Unknown tool: nope`. See the note on errors below.

> **A subtlety worth knowing — tool errors don't "throw".** When a tool call fails (unknown
> tool, wrong argument types), the MCP server does **not** raise an exception. It returns a
> normal result object with `isError = True` and the message in its content. So the client has
> to *check that flag* — see `/call` in `main.py`, where we turn `isError` into a clean HTTP
> 502. This matters: if you forget to check `isError`, failures look like successes.

---

## The two underlying files

### `server.py` — offers the tools

Three steps, that's the whole server:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-first-server")      # 1. create the server

@mcp.tool()                           # 2. register tools
def add(a: int, b: int) -> int:
    """Add two numbers together and return the result."""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio")        # 3. start it
```

**What is `transport="stdio"`?** The *transport* is just *how* the two programs send messages
to each other. `stdio` = standard input/output: the client launches the server as a
subprocess and they talk through that pipe. It's the simplest transport and needs no network,
no ports, no setup. (A later lesson shows the HTTP transport for servers that run remotely.)

### `client.py` — discovers and calls them

The client (using the official SDK's client side) does exactly the two things from Lesson 1:

```python
await session.initialize()                 # MCP handshake

tools = await session.list_tools()         # 1. DISCOVERY: "what do you offer?"

result = await session.call_tool("add", {"a": 2, "b": 3})   # 2. CALL a tool
print(result.content[0].text)              # -> "5"
```

Notice the client **hard-codes nothing about what the tools do**. It asks the server
(`list_tools`), then calls by name. Swap in a different server and the same client code finds
different tools.

> **Why does the result come back as `result.content[0].text`?** MCP tool results are a *list
> of content blocks* (so a tool could return text, an image, etc). Our tools return simple
> values, so the answer is the `.text` of the first block.

---

## Alternative: the plain script (`client.py`)

If you'd rather see the raw conversation in a terminal (no FastAPI, no browser), run the
script client. You only run the **client** — it starts the server for you.

```bash
cd mcp/lessons/02_your_first_server
python client.py
```

Expected output:

```
=== Tools the server offers ===
  • add: Add two numbers together and return the result.
  • greet: Return a friendly greeting for the given name.

=== Calling add(a=2, b=3) ===
  server returned: 5

=== Calling greet(name='Ada') ===
  server returned: Hello, Ada! Nice to meet you.
```

That's a full MCP round-trip: **discovery**, then two **tool calls**, across two separate
programs, with zero custom glue beyond "launch this command". `main.py` (Swagger) does the
exact same thing — it just gives you buttons instead of a script.

### If you want to see the server start on its own
```bash
python server.py
```
It just sits there silently — it's waiting to talk MCP over the pipe. There's nothing to see;
press `Ctrl+C`. (This proves the point: a server is useless without a client to drive it.)

---

## Setup / install

```bash
pip install "mcp>=1.2" "fastapi>=0.110" "uvicorn[standard]>=0.29"
```
`mcp` gives you *both* `mcp.server.fastmcp` (to build servers) and the client. `fastapi` +
`uvicorn` are only for the Swagger app (`main.py`); the plain script `client.py` needs just
`mcp`.

---

## Where's the LLM?

Not here on purpose. In this lesson **you** decided to call `add` then `greet` — you were the
brain. In Lesson 1's loop, that decision ("which tool, with what arguments?") is exactly the
part an **LLM** takes over. We'll add the LLM in a later lesson; everything you built here stays
the same, because the server doesn't care *who* its client is.

## Things to try (in Swagger)

1. Add a third tool to `server.py` — e.g. `multiply(a: int, b: int) -> int`. Restart uvicorn,
   hit `GET /tools`, and watch it appear **with no change to `main.py`**. That's discovery.
2. Delete the docstring from `greet`, restart, and look at `GET /tools` — its description goes
   blank. Proof that the docstring *is* the description the client receives.
3. In `POST /call`, send `{ "tool": "add", "arguments": {"a": "two", "b": 3} }` and watch the
   schema (built from your type hints) reject it with a 502 — before `add` ever runs.

## Next lesson

Lesson 3 — tools that take richer inputs and return structured data, plus what happens when a
tool fails (errors over MCP).
