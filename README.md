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
to building a production-ready API that calls an LLM like Claude. Explains **why FastAPI**
(and why not Flask or Django) for AI work. Eight runnable lessons, each with its own README;
**lessons 1–4 need no API key**, and lessons 5+ include a `MOCK_LLM` mode so the whole
course runs with zero cost.

**Covers:** what an API is (restaurant analogy) · HTTP methods & status codes · Pydantic
validation · async/await for slow LLM calls · calling Claude · streaming · conversation
memory · production concerns (config, CORS, logging, error handling, health checks).

See the [full course guide](fastapi-for-ai/README.md) for setup and how to run.

## Getting started

Each project has its own README with setup instructions. Most use
[`uv`](https://docs.astral.sh/uv/) for environment management:
```
