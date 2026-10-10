"""
Lesson 5 — Call a real LLM (via Groq) from your API.

Now everything comes together:
  * Pydantic validates the request (Lesson 3)
  * the endpoint is `async` so it scales (Lesson 4)
  * we `await` the Groq client to get the model's reply

Groq runs open models (Llama, etc.) on very fast hardware, with an
OpenAI-compatible chat API. It's free to start — great for learning.

MOCK MODE: if you have no API key (or set MOCK_LLM=true in .env), this returns a
fake reply so you can still run the lesson with no cost. Flip MOCK_LLM=false and
add your real key to call the model for real.

Setup:
    cp ../../.env.example ../../.env   # then edit it (or just leave MOCK_LLM=true)

Run it:
    uvicorn main:app --reload
Then open http://localhost:8000/docs
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# load_dotenv reads the .env file from the project root into environment vars.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
# Use mock mode if explicitly asked, OR if there's simply no key available.
MOCK = os.getenv("MOCK_LLM", "false").lower() == "true" or not os.getenv(
    "GROQ_API_KEY"
)

app = FastAPI(title="Lesson 5 — Call an LLM")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    max_tokens: int = Field(default=1024, ge=1, le=4096)


class ChatResponse(BaseModel):
    reply: str
    model: str
    mocked: bool


# Create the async client once, at startup, and reuse it for every request.
# (Creating a new client per request is wasteful.)
if not MOCK:
    from groq import AsyncGroq

    client = AsyncGroq()  # reads GROQ_API_KEY from the environment


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if MOCK:
        # No key / mock mode: pretend we called the model.
        return ChatResponse(
            reply=f"[MOCK REPLY] You asked: {req.message}",
            model=MODEL,
            mocked=True,
        )

    try:
        # The real call. `await` lets the server stay responsive while we wait.
        response = await client.chat.completions.create(
            model=MODEL,
            max_tokens=req.max_tokens,
            messages=[{"role": "user", "content": req.message}],
        )
    except Exception as exc:
        # Never let a provider error crash the server with an ugly 500.
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")

    # Groq's response is OpenAI-shaped: the text is in choices[0].message.content.
    reply_text = response.choices[0].message.content
    return ChatResponse(reply=reply_text, model=MODEL, mocked=False)


@app.get("/health")
def health():
    """Quick check: is the server up, and is it mocking or calling for real?"""
    return {"status": "ok", "model": MODEL, "mock_mode": MOCK}
