# Lesson 4 — LangGraph + MCP, end to end

**Goal:** finally add the **LLM** — and **build the LangGraph by hand** so you can see exactly
*where* a tool gets called inside the graph. In Lesson 2 *you* decided which tool to call; here
an **LLM node** decides and a **tool node** runs the MCP tool, wired together with a router edge.

This lesson has **two scripts that share the exact same graph**:

- **`agent.py`** — the graph driven against a server *you* wrote (`server.py`).
- **`github_agent.py`** — the *same graph*, pointed at the **real, remote GitHub MCP server**.
  Only the connection config changes. That it's that easy to swap servers **is** the point of MCP.

> Recap: a **server** offers tools, a **client** discovers and calls them. Until now the
> "brain" choosing tools was a human (you, or MCP Inspector). This lesson drops an **LLM** into
> that seat. **The server (`server.py`) doesn't change at all** — it never cares who its client is.

---

## Idea 1: the bridge

MCP tools and LangGraph speak different "dialects." Wiring them together by hand would mean:
connect to the server, do the handshake, list the tools, read each tool's schema, and wrap each
one so LangGraph can call it. Tedious — exactly the kind of glue MCP exists to kill.

**`langchain-mcp-adapters` is that glue, pre-written.** One object connects to your MCP server,
discovers its tools, and hands them back as LangChain tools a LangGraph node already understands.

```python
client = MultiServerMCPClient({"tools": {"command": sys.executable,
                                          "args": [SERVER_SCRIPT],
                                          "transport": "stdio"}})
tools = await client.get_tools()        # connect + discover + convert — all of Lesson 2's client.py
```

That `client` config dict is just Lesson 2's "how to launch the server" written as config.

---

## Idea 2: the graph (this is the new part)

Rather than a one-line prebuilt agent, we assemble a tiny **ReAct loop** so the tool call is
visible. It has **two nodes** and a **router**:

```
        ┌───────┐   has tool calls?   ┌───────┐
   START│ agent │────────── yes ─────►│ tools │
        │ (LLM) │◄───────────────────│ (MCP) │
        └───┬───┘   (result goes back)└───────┘
            │ no (final answer)
            ▼
           END
```

| Piece | What it is | Code |
|-------|-----------|------|
| **agent** node | the LLM; each turn it answers *or* emits a tool call | `llm.bind_tools(tools)` then `ainvoke` |
| **tools** node | runs whichever MCP tool the LLM asked for and appends the result | `ToolNode(tools)` — the one place a tool is actually called |
| **router** | reads the LLM's last message: tool call → `tools`, else → `END` | `should_call_tools()` + `add_conditional_edges` |
| **loop** | after `tools`, go back to `agent` so the LLM reads the result | `add_edge("tools", "agent")` |

`bind_tools` only *tells* the LLM which tools exist (so it may emit a call). `ToolNode` is where
the call actually runs, **inside the graph** — that's the thing this lesson makes visible.

---

## Files in this lesson

- `server.py` — the MCP **server** (3 tiny tools: `add`, `multiply`, `word_count`). Same style
  as Lessons 2–3; **no LLM, no LangGraph** inside it.
- `agent.py` — the MCP bridge + the **hand-built LangGraph** (`agent` node, `tools` node, router
  edge), run against the local `server.py`. This is the new code.
- `github_agent.py` — the **same graph**, pointed at GitHub's remote MCP server over HTTP. Diff
  it against `agent.py`: only the `MultiServerMCPClient` config differs.
- `requirements.txt` — deps for both scripts (nothing extra is needed for the remote server).
- `.env.example` — copy to `.env`; add your Groq key (and a GitHub token for `github_agent.py`).

---

## Setup

This is the first lesson that needs a key (a free **Groq** key — the open `gpt-oss` model).

```bash
cd mcp/lessons/04_langgraph_agent
pip install -r requirements.txt

cp .env.example .env        # then edit .env and paste your key(s)
```

Your `.env`:

```
GROQ_API_KEY=gsk_...                        # both scripts
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_... # only github_agent.py (part 2 below)
```

Get a free Groq key at <https://console.groq.com>. If a required secret is missing, the script
prints what to do and exits cleanly — it won't crash.

---

## Part 1 — run it against your own server

```bash
python agent.py
```

You start **only the agent**. It launches `server.py` for you as a subprocess (stdio), exactly
like the client in Lesson 2.

Expected output (wording from the LLM will vary):

```
=== Tools discovered from the MCP server ===
  • add: Add two numbers together and return the result.
  • multiply: Multiply two numbers together and return the result.
  • word_count: Count how many words are in a piece of text.

=== You: What is 23 plus 19? ===
Agent: 23 plus 19 is 42.
   (tools the graph called: add)

=== You: What is 6 times 7? ===
Agent: 6 times 7 is 42.
   (tools the graph called: multiply)

=== You: How many words are in the sentence 'MCP gives agents tools'? ===
Agent: There are 4 words.
   (tools the graph called: word_count)

=== You: Add 10 and 5, then tell me how many words are in the answer. ===
Agent: 10 + 5 = 15, and "15" is 1 word.
   (tools the graph called: add, word_count)
```

Notice two things. **Nobody told the graph which tool to use** — the LLM read each question and
the tool *descriptions* (your docstrings!) and chose. And the **last question used two tools**:
the `agent → tools → agent` loop ran twice before the LLM was satisfied. That loop is the graph
you built.

---

## How the pieces connect (one trip through the graph)

1. **Discovery** — `get_tools()` connects to `server.py`, does the MCP handshake, and lists the
   tools. (Same round-trip as Lesson 2's `client.py`, now one line.)
2. **`bind_tools`** — the tool schemas are given to the LLM so it's allowed to emit tool calls.
3. **START → agent** — the LLM runs on the conversation. It either answers or emits a tool call
   (`add` with `{"a": 23, "b": 19}`).
4. **router** — `should_call_tools` looks at that last message: a tool call sends us to `tools`;
   a plain answer sends us to `END`.
5. **tools node** — `ToolNode` runs the requested MCP tool **over the MCP protocol** and appends
   the result to the messages. *This is the only place a tool is actually called.*
6. **tools → agent** — back to the LLM, which reads the result and continues.

Steps 3–6 repeat until the LLM answers instead of calling a tool — that loop is what "agent" means.

---

## Why this matters

Your `server.py` is now usable by **three different clients** with zero changes:

- a human, via Swagger (Lesson 2),
- MCP Inspector (Lesson 3),
- an LLM agent (this lesson).

Write a tool once; any MCP-aware brain can drive it. That's the entire promise of MCP, now shown
end to end with a real LLM.

---

## Things to try

1. **Add a tool to `server.py`** — e.g. `subtract(a, b)`. Restart `agent.py` and ask "what is 50
   minus 8?". It appears in the discovery list and the LLM uses it — **with no change to the
   graph in `agent.py`**. That's discovery + MCP paying off.
2. **Break a docstring** — delete the docstring on `multiply`, restart, and ask a multiplication
   question. The LLM often gets confused, because the docstring *is* how it learns what the tool
   does. Proof that good descriptions matter for agents.
3. **Print the graph** — after `app = graph.compile()`, add
   `print(app.get_graph().draw_ascii())` to see the exact node/edge diagram the code built.
4. **Watch the loop** — print the whole `result["messages"]` list for the two-step question and
   read it top to bottom: user → LLM tool call → tool result → LLM tool call → tool result →
   final answer. That is `agent → tools → agent` running twice.
5. **Point at a real server** — swap the `MultiServerMCPClient` config to connect to a server you
   didn't write. That's exactly what **Part 2** does, below, with GitHub's MCP server.

---

## Part 2 — point the SAME graph at the real GitHub MCP server

Now the payoff. `github_agent.py` takes the graph you just built and connects it to GitHub's
official, remotely hosted MCP server — a server you **did not write**. The agent can suddenly
search repos, read files, and look at issues, with **no change to the graph code**.

### The one thing that changes: the connection

GitHub's server runs **somewhere else**, so you reach it over **HTTPS** instead of launching it
as a local subprocess. The only difference between the two scripts is this config dict:

```python
# agent.py — a local server you wrote (stdio transport)
"tools": {
    "command": sys.executable,
    "args": [SERVER_SCRIPT],
    "transport": "stdio",
}

# github_agent.py — GitHub's hosted server (streamable_http transport)
"github": {
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": {"Authorization": f"Bearer {pat}"},
    "transport": "streamable_http",
}
```

| Transport | Means | Used by |
|-----------|-------|---------|
| `stdio` | launch a local program, talk over its input/output pipe | `agent.py` (Lessons 2–4) |
| `streamable_http` | talk to a server running elsewhere, over HTTPS | `github_agent.py` |

Everything below that config — `bind_tools`, the `agent` node, the `tools` node (`ToolNode`),
the router, the loop — is **copied verbatim from `agent.py`**. Nothing in it knows the server is
GitHub's. That reusability is the whole point.

### Two secrets, two different jobs

- **`GROQ_API_KEY`** — authenticates **you to the LLM** (the agent's brain). Same as Part 1.
- **`GITHUB_PERSONAL_ACCESS_TOKEN`** — authenticates **the client to the MCP server**. It's sent
  as a `Bearer` token in the HTTP header so GitHub knows which repos you may see.

Make a **fine-grained** PAT at <https://github.com/settings/personal-access-tokens> with
**read-only** access to **public repositories** — that's all this needs. Don't grant write scopes.

### Run it

```bash
python github_agent.py
```

Expected output (tool list and wording will vary — GitHub's server changes over time):

```
=== Discovered 70+ tools from the GitHub MCP server ===
  • search_repositories
  • get_file_contents
  • list_issues
  … and many more

=== Using 5 tool(s) for this demo: search_repositories, get_file_contents, list_issues, get_issue, search_code ===

=== You: Search GitHub for the repository 'modelcontextprotocol/servers' and tell me what it is. ===
Agent: It's the official collection of reference MCP server implementations …
   (GitHub tools the graph called: search_repositories)
```

The agent discovered **dozens of real tools** it had never seen, picked the right ones, and
called them over the network — all with the Part 1 graph unchanged.

### Why `github_agent.py` filters the tool list

GitHub's server offers **many dozens** of tools. Handing all of them to a small model at once
makes it slower and more likely to pick the wrong one, so the script keeps a short read-only set:

```python
keep = {"search_repositories", "get_file_contents", "list_issues", "get_issue", "search_code"}
tools = [t for t in all_tools if t.name in keep] or all_tools
```

Delete those two lines to give the agent the full toolset — a realistic lesson in how tool count
affects an LLM's accuracy.

### More to try

- **Add a second server** — put BOTH the GitHub config *and* the local `server.py` config in the
  same `MultiServerMCPClient` dict. The agent then has GitHub tools **and** your `add` /
  `multiply` tools at once. That's what "MultiServer" means.
- **Local alternative (Docker)** — instead of the hosted URL, run GitHub's server locally with
  `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server` and
  connect over `stdio`. Same tools, different transport — more proof the agent doesn't care.

---

## Where this leaves you

You've now driven MCP servers of three kinds with the **same mental model** — and, across Parts 1
and 2, the **same agent graph**:

- one you wrote by hand (Lessons 2, 4),
- MCP Inspector against it (Lesson 3),
- a large, remote, third-party server (Part 2).

That's the full MCP promise, end to end: *write or find a tool server once; any MCP-aware
client — including an LLM agent — can plug in and use it, with no custom glue.*
