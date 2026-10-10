"""
Lesson 4 — async / await, and why slow LLM calls need it.

LLM calls are SLOW (often several seconds). The server spends that time just
waiting on the network. The question is: can it do other useful work while it
waits?

  * A normal (sync) function BLOCKS: the worker is frozen until it finishes.
  * An `async` function can `await` the slow bit and let the server go serve
    OTHER requests in the meantime.

This lesson has two endpoints that both "take 2 seconds". Open several browser
tabs and fire them at once to feel the difference.

Run it:
    uvicorn main:app --reload
Then open http://localhost:8000/docs
"""

import asyncio
import time

from fastapi import FastAPI

app = FastAPI(title="Lesson 4 — Async")


# ---- The SLOW, BLOCKING way -------------------------------------------------
# `time.sleep` freezes the worker. While this request sleeps, that worker
# cannot handle anyone else. Fire 5 of these at once and they queue up.
@app.get("/slow-blocking")
def slow_blocking():
    time.sleep(2)  # pretend this is a slow LLM / database / network call
    return {"done": "blocking", "waited_seconds": 2}


# ---- The ASYNC, NON-BLOCKING way -------------------------------------------
# `await asyncio.sleep(2)` tells the server "I'm waiting — go help others".
# Fire 5 of these at once and they all finish in ~2 seconds total, not 10.
# Real LLM SDKs give you `await client.chat.completions.create(...)` that works like this.
@app.get("/fast-async")
async def fast_async():
    await asyncio.sleep(2)  # pretend this is an AWAITABLE LLM call
    return {"done": "async", "waited_seconds": 2}


@app.get("/")
def explain():
    return {
        "try_this": "Open /docs, then hit /slow-blocking a few times quickly "
        "and compare with /fast-async. The async one stays responsive.",
    }
