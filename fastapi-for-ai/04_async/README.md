# Lesson 4 — async / await (why slow LLM calls need it)

**Goal:** understand why FastAPI's async support is its killer feature for AI work.

## The idea

LLM calls are **slow** — a response can take several seconds. During that time your server
is just *waiting on the network*. The question that decides whether your app scales:

> While waiting, can the server go help other users — or is it frozen?

- A normal **synchronous** function **blocks**: the worker is stuck until it returns.
- An **`async`** function can **`await`** the slow part and let the server serve other
  requests meanwhile.

```python
@app.get("/fast-async")
async def fast_async():
    await asyncio.sleep(2)   # "I'm waiting — go help others"
    return {...}
```

Real LLM SDKs give you an awaitable call — `await client.chat.completions.create(...)` — which is
exactly this. One server can keep hundreds of LLM requests in flight at once.

## Run it

```bash
uvicorn main:app --reload
```

## Feel the difference

Open <http://localhost:8000/docs>. There are two endpoints that both "take 2 seconds":

- `GET /slow-blocking` — uses `time.sleep` (freezes the worker)
- `GET /fast-async` — uses `await asyncio.sleep` (yields while waiting)

**Experiment:** open ~5 browser tabs. In all of them, hit the *same* endpoint at nearly the
same moment.

- With `/fast-async`, they all come back in ~2 seconds.
- With `/slow-blocking`, they tend to **queue** and finish one after another.

That queuing is what would wreck an LLM app under load.

## The rule of thumb

> If your endpoint `await`s something (an LLM call, a database query, another API),
> make it `async def`. If it only does fast CPU work, plain `def` is fine.

**Important gotcha:** never call a *blocking* function (like `time.sleep`, or a sync HTTP
library) inside an `async def` — it blocks the whole server. Use the `await`able version
instead. That's why we use async LLM clients in the next lessons.

## Things to try

1. Change both sleeps to 5 seconds and repeat the tab experiment — the gap is starker.
2. Add an `async` endpoint that `await`s *two* sleeps in a row and time it.
3. Read about `asyncio.gather` — running several awaits concurrently.

## Next

Lesson 5: put it all together and call a real LLM (via Groq) from your API.
