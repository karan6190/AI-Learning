# Lesson 5 — Call a real LLM from your API

**Goal:** build the "middle box" — your API receives a request, calls the LLM (via Groq),
returns the reply.

```
  browser  →  POST /chat (your FastAPI)  →  await Groq API  →  reply
```

Everything from the earlier lessons shows up here:
- **Pydantic** validates the request (Lesson 3)
- the endpoint is **`async`** so it scales while waiting (Lesson 4)
- we **`await`** the Groq client for the model's reply

Groq runs open models (like Llama) on very fast hardware with an OpenAI-compatible chat
API — and it's free to start, which makes it ideal for learning.

## No API key? No problem — MOCK mode

This lesson runs even without a key. If there's no `GROQ_API_KEY`, or you set
`MOCK_LLM=true`, the endpoint returns a *fake* reply so you can see the whole flow work at
zero cost.

To call the model for real:
1. From the course root, `cp .env.example .env`
2. Edit `.env`: paste your key into `GROQ_API_KEY` and set `MOCK_LLM=false`.
3. Get a free key at <https://console.groq.com/keys>.

## Run it

```bash
uvicorn main:app --reload
```
Open <http://localhost:8000/docs>.

First hit `GET /health` — it tells you whether you're in mock mode or calling for real.

## Try it

Send to `POST /chat`:
```json
{ "message": "Explain what an API is in one sentence." }
```

- **Mock mode:** you get `[MOCK REPLY] You asked: ...` and `"mocked": true`.
- **Real mode:** you get the model's actual answer and `"mocked": false`.

## What to notice

- The async client is created **once** at startup (`client = AsyncGroq()`) and reused —
  not rebuilt per request.
- The real call is `await client.chat.completions.create(...)` — the awaitable from Lesson 4.
- The response text lives at `response.choices[0].message.content`.
- We wrap the call in `try/except` and raise a clean **502** if the provider fails — your
  server should never crash because an upstream API hiccuped.
- The API key is read from the environment, **never hard-coded**. `.env` is git-ignored.

## Key safety (say this to students)

- Never put your API key in the source code.
- Never commit `.env`.
- The key is a password that spends real money — treat it like one.

## Things to try

1. Add a `system` prompt field to `ChatRequest` and send it as the first message with
   `{"role": "system", "content": ...}` ahead of the user message.
2. Return the token usage (`response.usage`) in the response so you can see cost per call.
3. Turn off mock mode and watch latency — then recall *why* async matters (Lesson 4).

## Next

Lesson 6: **streaming** — send the reply token-by-token so the UI feels instant (the
ChatGPT typing effect).
