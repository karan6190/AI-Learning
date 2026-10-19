# AI Projects

A collection of hands-on AI learning and teaching projects.

## Projects

### 📚 [Multi-Agent Systems with LangGraph](Multi-agent-parallel-execution/)

A beginner-friendly course on building **supervisor-based multi-agent systems
with parallel execution** in [LangGraph](https://langchain-ai.github.io/langgraph/).
Designed for teaching — every lesson is runnable, and lessons 1–4 need no API key.

**Covers:** supervisor node & routing logic · agent hand-off & task delegation ·
subgraphs as reusable agent components · parallel execution (fan-out / fan-in).

See the [full course guide](Multi-agent-parallel-execution/README.md) for details.

### 🔍 [LangSmith Tracing — Hands-On Demo](langsmith/)

A teaching kit for setting up **LangSmith tracing** and using it to read
**latency**, **token usage**, **errors in a trace**, and to **debug an agent
loop**. Five runnable demos, each mapped to a screen in the LangSmith UI, plus a
facilitator's guide and live talking points. Runs on **Groq** (the open
**gpt-oss** model) — no OpenAI key needed.

**Covers:** turning tracing on with 3 env vars · reading the waterfall / per-step
latency · token usage & cost · failed runs and stack traces · inspecting an agent's
reasoning loop.

See the [demo guide](langsmith/README.md) for setup and how to run.

### ⚡ [FastAPI for AI — From Basic APIs to Calling LLMs](fastapi-for-ai/)

A hands-on course that takes complete beginners from *"what even is an API?"* all the way
to building a production-ready API that calls an LLM (on **Groq** — fast and free to start).
Explains **why FastAPI** (and why not Flask or Django) for AI work. Nine runnable lessons,
each with its own README; **lessons 1–4 need no API key**, and lessons 5+ include a
`MOCK_LLM` mode so the whole course runs with zero cost.

**Covers:** what an API is (restaurant analogy) · HTTP methods & status codes · Pydantic
validation · async/await for slow LLM calls · calling the LLM · streaming · conversation
memory · production concerns (config, CORS, logging, error handling, health checks) ·
prompt injection through tool output & input/output guardrails.

See the [full course guide](fastapi-for-ai/README.md) for setup and how to run.

### 🔌 [MCP — Giving AI Agents Tools Through a Standard Protocol](mcp/)

A from-zero course on the **Model Context Protocol (MCP)** — the "USB-C for AI tools" that lets
any AI app plug into any set of tools without custom glue. Starts with the mental model (no
code), then builds a real MCP **server** with **FastMCP** and tests it from a **Swagger** page,
before adding an LLM so the agent chooses tools itself. Runnable offline with no key.

**Covers:** what MCP is & why it exists (server vs client, discovery vs calling) · building a
server with FastMCP (type hints → tool schema) · the stdio transport · testing tools via a
FastAPI/Swagger client · tool errors over MCP (`isError`) · (coming) an LLM-driven agent and
the real GitHub MCP server.

See the [full course guide](mcp/README.md) for setup and how to run.

## Getting started

Each project has its own README with setup instructions. Most use
[`uv`](https://docs.astral.sh/uv/) for environment management:

```bash
cd <project-folder>
uv venv
uv pip install -r requirements.txt
```
