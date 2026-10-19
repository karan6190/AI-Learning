# MCP — Giving AI Agents Tools Through a Standard Protocol

A hands-on course, from zero, on the **Model Context Protocol (MCP)** — the standard that lets
an AI app plug into any set of tools (GitHub, a database, your files…) **without writing custom
glue for each one**. Think of it as **USB-C for AI tools**.

Every lesson is small and **runnable**, with its own `README.md`. Work through them in order —
each adds one idea on top of the last. The early lessons run **offline with no API key**.

---

## Who this is for

People who have heard "MCP" and want to actually understand it:

1. What MCP *is* (it's a protocol, not a library or a model) and **why** it exists.
2. The two roles: a **server** that offers tools, a **client** that uses them.
3. How to **build** a server with **FastMCP** (one decorator per tool).
4. How to **test** it — from a plain script and from a **Swagger `/docs`** page.
5. (Coming) How an **LLM** drives the client, and how to connect the **real GitHub MCP server**.

Basic Python helps. No prior MCP knowledge assumed.

---

## The one idea

An LLM on its own is a **text-in, text-out** machine — a brilliant brain with no arms. **Tools**
give it arms: functions it can ask to run (read a file, call an API). Before MCP, every app
wired up every tool its own way, with no reuse. **MCP standardises that connection** so a tool
built once works in any MCP-aware app.

```
   ┌─────────────┐   "what tools do you have?"    ┌─────────────┐
   │ MCP CLIENT  │  ───────────────────────────►  │ MCP SERVER  │
   │ (your app,  │  ◄──  list of tools  ─────────  │ (offers the │
   │  later + an │  ───  "run add(2,3)"  ───────►  │   tools)    │
   │   LLM)      │  ◄──  5  ──────────────────────  │             │
   └─────────────┘                                 └─────────────┘
     decides WHICH tool                              actually DOES the work
```

---

## The lessons

| # | Folder | What you learn |
|---|--------|----------------|
| 1 | [`lessons/01_what_is_mcp`](lessons/01_what_is_mcp) | The mental model — what MCP is & why (no code): tools, agents, server vs client, discovery vs calling |
| 2 | [`lessons/02_your_first_server`](lessons/02_your_first_server) | Build the smallest MCP server with **FastMCP**; test it from **Swagger** and from a script |

More lessons coming: richer tool inputs & errors, an **LLM-driven agent** that chooses tools,
and connecting the **real GitHub MCP server**.

Each folder has its own `README.md` with the concept, the code walk-through, and things to try.

---

## Setup

### 1. Install Python 3.10+
Check with `python --version`.

### 2. Create a virtual environment
```bash
# from inside the mcp folder
python -m venv .venv

# activate it:
#   Windows (Git Bash):   source .venv/Scripts/activate
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   macOS / Linux:         source .venv/bin/activate
```

### 3. Install the dependencies
```bash
pip install "mcp>=1.2" "fastapi>=0.110" "uvicorn[standard]>=0.29"
```
- `mcp` gives you **both** sides: `mcp.server.fastmcp` (to build servers) and the client.
- `fastapi` + `uvicorn` are for the **Swagger** test app in Lesson 2 (`main.py`).

Lessons 1–2 need **no API key**. (Later LLM lessons will use a free **Groq** key, with a mock
mode so you can still run them with no cost.)

---

## How to run a lesson

Each lesson's README has exact commands. In short:

**Swagger (recommended) — test tools by clicking:**
```bash
cd lessons/02_your_first_server
uvicorn main:app --reload
# then open http://localhost:8000/docs
```

**Plain script — see the bare client/server conversation in a terminal:**
```bash
cd lessons/02_your_first_server
python client.py
```

---

## Glossary

- **MCP** — Model Context Protocol: the standard rules an AI app and a set of tools follow.
- **Tool** — a function the model can ask to run (your code actually runs it).
- **Agent** — an LLM in a loop that can call tools, read results, and decide what to do next.
- **MCP server** — a program that *offers* tools.
- **MCP client** — a program that *discovers and calls* those tools (on an LLM's behalf).
- **FastMCP** — a Python library to build MCP servers; one decorator turns a function into a tool.
- **Transport** — *how* client and server exchange messages. `stdio` = over a subprocess pipe.
- **Discovery** — the client asking the server, at connect time, what tools it has.

---

## One sentence to remember

> *MCP is USB-C for AI tools: write a tool once as a server, and any MCP-aware client — yours or
> someone else's — can plug in and use it, with no custom glue.*
