# FastAPI for AI — From Basic APIs to Calling LLMs

A hands-on course that takes you from *"what even is an API?"* all the way to building a
production-ready API that talks to a Large Language Model (LLM). The LLM calls run on
**Groq** — fast, free to start, and running open models like Llama.

Every lesson is a small, **runnable** FastAPI app with its own `README.md`. Work through
them in order — each one adds exactly one new idea on top of the last.

---

## Who this is for

People who are new to APIs and want to understand:

1. What an API actually *is* (no jargon).
2. How web APIs and HTTP work.
3. Why AI apps need APIs at all.
4. **Why FastAPI** is the default choice for AI/LLM work (and why not Flask or Django).
5. How to build your own API that calls an LLM.

No prior API experience needed. Basic Python helps.

---

## Part 1 — What is an API?

**API = Application Programming Interface.** It's a *contract* that lets two pieces of
software talk to each other without either one knowing how the other works inside.

### The restaurant analogy

| In a restaurant | In software |
|-----------------|-------------|
| You at the table | The **client** (a browser, a mobile app, another program) |
| The menu | The **API documentation** — what you're allowed to ask for |
| The waiter | The **API** — carries your request in, brings the response back |
| The kitchen | The **server / backend** — does the work, you never see it |

You don't walk into the kitchen and cook. You make a **request** in an agreed format and
get a **response**. That's an API.

APIs are everywhere: a weather app calls a weather API, "Log in with Google" is an API,
and the AI chatbot you'll build calls an LLM through an API.

---

## Part 2 — Web APIs & HTTP (the vocabulary)

Most APIs today are **web APIs** spoken over **HTTP**. Four things to know:

**1. The method (the verb) — what you want to do:**

| Method | Meaning | Example |
|--------|---------|---------|
| `GET` | fetch something | get a list of users |
| `POST` | create / send data | submit a chat message |
| `PUT` / `PATCH` | update something | edit a profile |
| `DELETE` | remove something | delete a message |

**2. The endpoint (the noun) — the address:** `https://api.example.com/users/42`

**3. The body — usually JSON — the data you send/receive:**
```json
{ "message": "Explain photosynthesis", "model": "llama-3.3-70b-versatile" }
```

**4. The status code — the outcome:** `200` OK · `404` not found · `422` you sent bad data · `500` server broke.

> **Try it:** open any website, press F12 → **Network** tab, reload. You're watching real
> HTTP requests and responses fly back and forth.

---

## Part 3 — Why do AI / LLMs need APIs?

An LLM lives on **someone else's giant servers** (Groq, OpenAI, Anthropic, …). You can't
run it on your laptop. So your app *calls it over an API*.

But you also build your **own** API — the layer between your users and the LLM:

```
  User's browser  →  YOUR API (FastAPI)  →  LLM provider API  →  and back again
                     ^^^^^^^^^^^^^^^^^^^
                     this is what you build
```

Your API is where the real value lives: authentication, rate limiting, prompt templates,
logging, cost control, and combining the LLM with your own data (RAG). **You build the
middle box — and FastAPI is excellent at it.**

---

## Part 4 — Why FastAPI? (and why not the others)

Python has several ways to build an API. Here's why FastAPI became *the* default for AI:

| Framework | Good at | Why it's less ideal for LLM APIs |
|-----------|---------|----------------------------------|
| **Flask** | Simple, minimal, huge ecosystem | No built-in validation, no async by default, no auto docs — you bolt it all on by hand |
| **Django / DRF** | Batteries-included, big database-heavy sites | Heavy and opinionated; more than a thin AI service needs; async is bolted-on |
| **FastAPI** | Modern, async-first, validation + docs built in | *This is the point* ↓ |

**The four reasons FastAPI wins for AI work:**

1. **Async is first-class → it handles *waiting* well.** LLM calls are slow (seconds). While
   waiting, FastAPI does useful work, so one server handles hundreds of in-flight requests.
2. **Type hints + Pydantic → automatic validation.** You declare the shape of a request and
   FastAPI *enforces* it. Bad data is rejected before it reaches your LLM (which costs money per call).
3. **Automatic interactive docs.** A live, clickable test page at `/docs` — for free.
4. **Speed + ecosystem fit.** One of the fastest Python frameworks, and the AI tooling
   (LangServe, templates, tutorials) already speaks FastAPI.

You'll *feel* each of these as you move through the lessons.

---
## Setup (do this once)

### 1. Install Python 3.10+
Check with `python --version`.

### 2. Create a virtual environment
```bash
# from inside the fastapi-for-ai folder
python -m venv .venv

# activate it:
#   Windows (Git Bash):   source .venv/Scripts/activate
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   macOS / Linux:         source .venv/bin/activate
```

### 3. Install the dependencies
```bash
pip install -r requirements.txt
```

### 4. (For lessons 5+) Add your API key

**On GitHub Codespaces:** if `GROQ_API_KEY` is set as a Codespaces secret (with access
granted to this repo), it's already in the environment — **you don't need a `.env` file**.
Skip this step. (Check it worked by hitting `GET /health` on any lesson 5+ app: it reports
`"mock_mode": false` when the key is live.)

**Running locally:**
```bash
cp .env.example .env
# then open .env and paste your Groq API key
```

Get a free key at <https://console.groq.com/keys>. **Lessons 1–4 need no key at all** — and
lessons 5+ include a `MOCK_LLM` mode so you can run them even without one.

> How the key is found: the code reads `os.getenv("GROQ_API_KEY")`. `load_dotenv()` fills
> that in from a `.env` file *if one exists*, but it never overrides a real environment
> variable — so a Codespaces/CI secret always takes precedence and no `.env` is required.

---

## How to run any lesson

```bash
cd lessons/01_hello_api
uvicorn main:app --reload
```

Then open **<http://localhost:8000/docs>** in your browser. That's the interactive docs —
you can call every endpoint from there without writing any client code.

- `uvicorn` is the server that runs your app.
- `main:app` means "in the file `main.py`, use the variable named `app`".
- `--reload` restarts automatically when you edit the code (great for learning).

Stop the server with `Ctrl+C`.

---

## Glossary

- **API** — a contract for software to talk to software.
- **Endpoint / route** — one specific URL your API responds to (e.g. `/chat`).
- **Request / Response** — what the client sends / what the server sends back.
- **JSON** — the text format used to carry data (`{"key": "value"}`).
- **HTTP method** — the verb: GET, POST, etc.
- **Status code** — a number saying how it went (200, 404, 500…).
- **Pydantic** — the library FastAPI uses to validate data shapes.
- **async / await** — Python's way to do other work while waiting on slow things.
- **LLM** — Large Language Model, e.g. Llama on Groq. Lives behind a provider's API.
- **Uvicorn** — the web server that actually runs your FastAPI app.
- **Swagger UI** — the interactive docs page served at `/docs`.

---

## One sentence to remember

> *An API is how software talks to software; FastAPI is the fastest, clearest way in Python
> to build the API that stands between your users and an LLM.*