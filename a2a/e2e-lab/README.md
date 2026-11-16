# A2A + MCP Observability Lab — Follow One Request Through Every Agent and Tool

When one agent calls another agent, which then calls a tool, it's hard to answer
questions like **"why was that slow?"** or **"where did it fail?"** Each piece runs in its
own process and writes its own logs.

**Tracing** fixes this. Every step records a **span** (a named, timed step). All the spans
from one user request share **one trace ID**, so you can put them together into a single picture.

In this lab you build that picture for a small multi-agent system:

```
                          A2A                          MCP
  Supervisor  ─────────────────────►  Weather Agent  ─────────►  ┌──────────────────┐
  "Plan my trip                                                   │ MCP tool server  │
   to Paris,              A2A                          MCP        │  get_weather     │
   500 USD"   ─────────────────────►  Currency Agent ─────────►  │  convert_currency│
                                                                  └──────────────────┘
  └── process 3 ──┘                 └──── process 2 ────┘          └──── process 1 ────┘

                      ONE trace ID travels along every arrow
```

**No API key and no Docker.** Everything runs locally with plain Python.

> **New to A2A or MCP?** Do the [A2A lab](../lab/README.md) and the
> [MCP course](../../mcp/README.md) first. This lab reuses both patterns and only adds tracing.

---

## The 4 ideas you need

| Idea | In plain words | In this lab |
|---|---|---|
| **Span** | One timed step: a name, a start, an end, and some notes (attributes) | `agent Weather Agent`, `tool get_weather`, ... |
| **Trace** | All the spans for one user request, arranged as a tree | everything under `plan trip` |
| **Trace ID** | The ID every span in the trace shares | printed by the supervisor, e.g. `0b38d652...` |
| **Propagation** | Passing the trace ID to the next process so it can join the trace | `traceparent` in A2A `metadata` and MCP `_meta` |

Propagation is the only part that's new. Without it you'd get **3 separate traces** that
nobody can connect. With it you get **one trace**.

---

## Files

| File | Role | Runs as |
|---|---|---|
| [`telemetry.py`](telemetry.py) | Shared tracing setup: `setup_tracing()`, `inject_trace()`, `continue_trace()` | imported by all |
| [`01_mcp_server.py`](01_mcp_server.py) | **MCP server** with 2 tools. Reads the trace ID from MCP `_meta` | terminal 1 |
| [`02_a2a_agents.py`](02_a2a_agents.py) | **2 A2A agents** (servers) that are also **MCP clients** | terminal 2 |
| [`03_supervisor.py`](03_supervisor.py) | **Supervisor**: starts the trace, discovers agents, calls both in parallel | terminal 3 |
| [`04_view_trace.py`](04_view_trace.py) | Draws the trace as a waterfall in your terminal | terminal 3 |

---

## Setup

```bash
# from inside the a2a folder
python -m venv .venv
#   Windows (Git Bash):    source .venv/Scripts/activate
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   macOS / Linux:         source .venv/bin/activate
pip install -r requirements.txt
```

> **Note:** we pin `mcp<2`. MCP 2.x renamed `FastMCP`, and this lab uses the same 1.x API as the MCP course.

---

## Run it (3 terminals)

```bash
# terminal 1 — the tools
python observability_lab/01_mcp_server.py

# terminal 2 — the agents
python observability_lab/02_a2a_agents.py

# terminal 3 — send a request, then look at the trace
python observability_lab/03_supervisor.py
python observability_lab/04_view_trace.py
```

### What the supervisor prints

```
User: Plan my trip to Paris, my budget is 500 USD
Trace ID: 0b38d652184902996af50dacaf877111

STEP 1 · discovering agents...
  skill get_weather       -> Weather Agent
  skill convert_currency  -> Currency Agent

STEP 2 · asking both agents in parallel over A2A...

STEP 3 · answer:
  Weather in Paris: 24°C and rainy
  Budget: 500 USD = 462.96 EUR
```

Look at terminals 1 and 2. Every log line starts with the **same** `[trace 0b38d652]`.
That's the trace ID arriving in other processes.

### What the trace viewer prints

```
Trace 0b38d652184902996af50dacaf877111   (12 spans, 1095 ms)

SPAN                                         SERVICE             TIME   TIMELINE
plan trip                                    supervisor        1095ms   ██████████████████████████████
├─ discover agents                           supervisor         406ms   ███████████
├─ a2a SendMessage -> Weather Agent          supervisor         677ms              ███████████████████
│  └─ agent Weather Agent                    a2a-agents         601ms                ████████████████
│     └─ mcp call_tool get_weather           a2a-agents         599ms                ████████████████
│        ├─ mcp initialize session           a2a-agents          57ms                ██
│        └─ tool get_weather                 mcp-tool-server     50ms                   █
└─ a2a SendMessage -> Currency Agent         supervisor         658ms              ██████████████████
   └─ agent Currency Agent                   a2a-agents         585ms                ████████████████
      └─ mcp call_tool convert_currency      a2a-agents         583ms                ████████████████
         ├─ mcp initialize session           a2a-agents          32ms                 █
         └─ tool convert_currency            mcp-tool-server    401ms                    ███████████

Details (inputs/outputs recorded on each span):
  tool convert_currency
      tool.input.amount = 500.0
      tool.input.from = USD
      tool.input.to = EUR
      tool.output = 500 USD = 462.96 EUR
  ...
```

### How to read it

- **The tree = who called whom.** Indentation shows the path: supervisor → A2A → agent → MCP → tool.
- **The SERVICE column = which process.** Three different processes, one tree. That's propagation working.
- **The bars = when.** The two `a2a SendMessage` bars **overlap**, so the two agents ran **in parallel**
  (`asyncio.gather` in the supervisor).
- **The longest bar at the bottom = the bottleneck.** `tool convert_currency` takes 400 ms
  (it sleeps on purpose to imitate a slow exchange-rate API). The whole Currency branch waits on it.
- **The Details = what went in and out** of each hop, so you can debug without adding print statements.

Your timings will differ. Run the supervisor a few times and compare with `--list`.

---

## How the trace ID travels (the only new code)

There are 3 small helpers in [`telemetry.py`](telemetry.py), used at each hop:

```
  SENDER                                              RECEIVER
  inject_trace()  ──► {"traceparent": "00-<trace id>-<span id>-01"}  ──►  continue_trace(...)
  "copy my trace ID into a dict"                       "start my span inside the caller's trace"
```

`traceparent` is a [W3C standard](https://www.w3.org/TR/trace-context/) header, so any
tracing tool understands it.

### Hop 1 — Supervisor → Agent (A2A)

The supervisor puts the trace ID in the A2A request's **`metadata`** ([`03_supervisor.py`](03_supervisor.py)):

```python
request = SendMessageRequest(message=new_text_message(question, role=Role.ROLE_USER))
request.metadata.update(inject_trace())          # <-- add traceparent
```

On the wire it's ordinary A2A JSON-RPC:

```json
{ "jsonrpc": "2.0", "method": "SendMessage",
  "params": {
    "message":  { "role": "ROLE_USER", "parts": [ { "text": "Convert 500 USD to EUR" } ] },
    "metadata": { "traceparent": "00-0b38d652184902996af50dacaf877111-5f1c...-01" } } }
```

The agent reads it back ([`02_a2a_agents.py`](02_a2a_agents.py)):

```python
with continue_trace(tracer, context.metadata, f"agent {self.name}"):
    answer = await self.brain(question)
```

### Hop 2 — Agent → Tool (MCP)

The agent passes the trace ID in the MCP request's **`_meta`** field ([`02_a2a_agents.py`](02_a2a_agents.py)):

```python
result = await session.call_tool(tool, arguments, meta=inject_trace())   # <-- add traceparent
```

```json
{ "jsonrpc": "2.0", "method": "tools/call",
  "params": { "name": "convert_currency",
              "arguments": { "amount": 500, "from_ccy": "USD", "to_ccy": "EUR" },
              "_meta": { "traceparent": "00-0b38d652184902996af50dacaf877111-a2b7...-01" } } }
```

The tool reads it back ([`01_mcp_server.py`](01_mcp_server.py)):

```python
with continue_trace(tracer, trace_carrier(ctx), "tool convert_currency"):
    ...
```

**That's all.** Two lines to send and two lines to receive, and three processes become one trace.

> **Why `metadata` and `_meta`?** Both protocols set aside a field for exactly this kind
> of extra information. Putting the trace ID there means it works over any transport and
> through any proxy.

---

## Exercises

### 1 · See a failure in the trace

```bash
python observability_lab/03_supervisor.py Atlantis 200 GBP
python observability_lab/04_view_trace.py
```

```
│     └─ mcp call_tool get_weather    a2a-agents   647ms  ███████  ✗ Error executing tool get_weather: Unknown city: 'Atlantis'
│        └─ tool get_weather          mcp-tool-server 130ms  ███  ✗ ValueError: Unknown city: 'Atlantis'
```

The failed spans are shown in **red**, and the error is on the exact hop where it happened. The
Currency branch still succeeded, so the trace shows a **partial failure** that logs alone would hide.
Run `04_view_trace.py --list` and you'll see this trace in the `ERRORS` column.

### 2 · Find the bottleneck

Run `python observability_lab/03_supervisor.py Tokyo 300 JPY`. Which span is the longest leaf?
Change `time.sleep(0.4)` in `convert_currency` to `0.05`, restart terminal 1, and run again.
How much faster is the **whole** request? (Hint: the two branches run in parallel, so the
total is set by the **slower** branch, not by the sum of both.)

### 3 · Find the time nobody named

Look at `mcp call_tool get_weather` (~600 ms). Its children (`initialize session` + `tool`)
add up to only ~110 ms. Where did the other ~490 ms go? Wrap `streamablehttp_client(...)`
in its own span (copy the `mcp initialize session` pattern) and run again.
*Lesson: a gap between a parent and its children means some work has no span yet.*

### 4 · Break propagation on purpose

In `02_a2a_agents.py`, change `meta=inject_trace()` to `meta=None`. Restart terminal 2 and
run the supervisor. Then run `04_view_trace.py --list`: the tool spans now show up as
**separate traces** that you can't connect to the request. Put the line back.

### 5 · Make it sequential

In `03_supervisor.py`, replace the `asyncio.gather(...)` with two plain `await ask_agent(...)` calls.
Compare the waterfall: the bars no longer overlap, and the total time goes up.

### 6 · Look at the SDK's own spans

The A2A SDK has built-in tracing for its internals. We switch it off in `telemetry.py` to
keep the picture simple. To see it, set the variable before starting the agents:

```bash
OTEL_INSTRUMENTATION_A2A_SDK_ENABLED=true python observability_lab/02_a2a_agents.py
```

Notice how much noise that adds. Choosing *what* to trace is part of good observability.

---

## Optional · View the same trace in a real tracing UI

The lab always writes spans to `observability_lab/traces.jsonl`. If you also set
`OTEL_EXPORTER_OTLP_ENDPOINT`, every process **also** sends its spans over **OTLP**, the
standard OpenTelemetry protocol. Any OTLP backend can show them. No code changes are needed.

**Jaeger (open source, runs locally).** Download the single `jaeger` binary from
[jaegertracing.io/download](https://www.jaegertracing.io/download/) and run it, or use
`docker run --rm -p 16686:16686 -p 4318:4318 jaegertracing/jaeger:latest` if you have Docker.
Then, in **each** of the 3 terminals before starting the script:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Open http://localhost:16686, choose service `supervisor`, and click your trace.

**LangSmith.** LangSmith accepts OpenTelemetry traces (see the [LangSmith tracing demo](../../langsmith/README.md)):

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.smith.langchain.com/otel
export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=<your-langsmith-key>,Langsmith-Project=a2a-observability"
```

> Check the current OTLP endpoint in the [LangSmith docs](https://docs.smith.langchain.com/)
> if this doesn't work. EU and self-hosted instances use a different host.

---

## Useful commands

```bash
python observability_lab/04_view_trace.py --list          # all traces, with span count, time, errors
python observability_lab/04_view_trace.py 0b38d652        # one trace (first chars of the ID are enough)
python observability_lab/04_view_trace.py --clear         # start fresh
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `no agent at http://127.0.0.1:920x` | Terminal 2 isn't running (or was started before terminal 1 finished) |
| `Weather in Paris: (tool error: ...connect...)` | Terminal 1 (the MCP server) isn't running |
| Trace shows only `supervisor` spans | The agents were started from an old version; restart terminals 1 and 2 |
| `No module named 'mcp.server.fastmcp'` | You have MCP 2.x: `pip install "mcp<2"` |
| Strange characters like `[31m` in the output | Your terminal doesn't support colour; the content is still correct |

## Recap

1. **Span** = one timed step. **Trace** = all spans of one request. **Trace ID** joins them.
2. **Propagation** is what makes multi-agent tracing work: `inject_trace()` on the sending side, `continue_trace()` on the receiving side.
3. **A2A** carries the trace ID in `metadata`. **MCP** carries it in `_meta`.
4. A waterfall answers the real questions: *what ran in parallel, what was slow, what failed, and with which inputs*.
