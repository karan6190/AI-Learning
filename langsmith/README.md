# LangSmith Tracing — Hands-On Demo

A teaching kit for setting up LangSmith tracing and using it to read **latency**,
**token usage**, **errors in a trace**, and to **debug an agent loop**.

Runs on **Groq** (the open **gpt-oss** model) — no OpenAI key needed.

---

## What's in this folder

| File | What it's for |
|------|---------------|
| `README.md` | This file — setup + how to run |
| `requirements.txt` | Python dependencies |
| `.env` | Tracing config (`LANGSMITH_TRACING`, `LANGSMITH_PROJECT`) — **no secrets** |
| `.env.example` | Template showing all the vars |
| `01_setup_first_trace.py` | Your first trace |
| `02_latency.py` | Reading latency / the waterfall |
| `03_token_usage.py` | Token usage & cost |
| `04_error_trace.py` | Errors in a trace |
| `05_agent_loop.py` | Debugging an agent loop |
| `TALKING_POINTS.md` | What to click & say on each screen (live) |
| `TEACHING_GUIDE.md` | How to run the whole session (facilitator) |

---

## Session flow (suggested ~60 min)

| # | Topic | File | What you'll show in the LangSmith UI |
|---|-------|------|--------------------------------------|
| 1 | Setup & first trace | `01_setup_first_trace.py` | A run appears under your project; open it, see inputs/outputs |
| 2 | Latency | `02_latency.py` | Per-step latency, waterfall view, slow child spans |
| 3 | Token usage & cost | `03_token_usage.py` | Prompt/completion tokens, aggregate in project |
| 4 | Errors in a trace | `04_error_trace.py` | Red/failed run, exception + stack trace on the span |
| 5 | Debug an agent loop | `05_agent_loop.py` | Nested tool calls, the reasoning loop, where it goes wrong |

---

## Prerequisites

1. A LangSmith account → https://smith.langchain.com (Settings → API Keys → create a key).
2. A Groq API key → https://console.groq.com/keys
3. Python 3.9+.

---

## How keys & config are split

This kit is set up for **GitHub Codespaces**, so we split the two kinds of values:

- **Secrets (the keys)** live in **Codespace secrets** — they're injected into the
  environment automatically, so they never sit in a file in the repo:
  - `LANGSMITH_API_KEY`
  - `GROQ_API_KEY`
- **Config (not secret)** lives in **`.env`** and is loaded by `load_dotenv()`:
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_PROJECT=langsmith-demo`

> Not using Codespaces? Just put all four values in `.env` (see `.env.example`).
> `load_dotenv()` won't overwrite anything already set in the environment, so the
> two approaches mix safely.

---

## Setup

```bash
cd langsmith
python -m venv .venv
source .venv/Scripts/activate      # Git Bash / Codespaces
pip install -r requirements.txt
```

The `.env` (tracing config) is already in the folder:

```
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langsmith-demo
```

Make sure your two keys are available as Codespace secrets (or add them to `.env`).

> **LLM provider:** demos use **Groq** running the open **gpt-oss** model
> (`openai/gpt-oss-20b`) via `langchain_groq.ChatGroq`. The **model is chosen on one
> line** near the top of each script — change the `model=` string to swap it
> (e.g. `openai/gpt-oss-120b` or `llama-3.3-70b-versatile`). The LangSmith tracing
> parts are provider-independent — that's the point of the session.

---

## The one thing that turns tracing on

Set these before your code runs:

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=...
```

LangChain/LangGraph auto-instrument — no code changes. For plain Python functions,
add one `@traceable` decorator (shown in `03` and `05`). That's the whole setup.

**You do NOT need to create the project manually** — LangSmith auto-creates
`langsmith-demo` the first time a trace is sent.

---

## Running

```bash
python 01_setup_first_trace.py
```

Then open https://smith.langchain.com → project **`langsmith-demo`** → newest run.

Run the rest in order (`02` … `05`), opening each run in the UI as you go.
See `TALKING_POINTS.md` for what to highlight on each screen.

---

## Verify your setup (run this first if nothing appears)

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; \
print('tracing =', repr(os.environ.get('LANGSMITH_TRACING'))); \
print('LS key  =', bool(os.environ.get('LANGSMITH_API_KEY'))); \
print('Groq key=', bool(os.environ.get('GROQ_API_KEY'))); \
print('project =', os.environ.get('LANGSMITH_PROJECT')); \
print('endpoint=', os.environ.get('LANGSMITH_ENDPOINT'))"
```

Expected: `tracing = 'true'`, both keys `True`, `project = langsmith-demo`.

---

## Troubleshooting — "nothing shows up in LangSmith"

1. **`LANGSMITH_TRACING` must be the string `true`** (lowercase). If it's `None`,
   nothing is traced. This is the #1 cause.
2. **Region mismatch.** `smith.langchain.com` is the **US** portal. If your key is
   from an **EU** account, add `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`
   to `.env` and view traces at **eu.smith.langchain.com**.
3. **Did the script print an answer?** If it errored, the model call failed so there
   was no trace to send — fix that error first (check `GROQ_API_KEY`).
4. **Traces not flushed** on very short scripts — force it:
   ```python
   from langchain_core.tracers.langchain import wait_for_all_tracers
   wait_for_all_tracers()
   ```
5. **Check the project name** matches exactly (case-sensitive) between `.env` and
   the UI.
