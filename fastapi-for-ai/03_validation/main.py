"""
Lesson 3 — Validation with Pydantic.  (The "why not Flask?" moment.)

You declare the SHAPE of a request as a class, and FastAPI enforces it for you:
  * missing field?        -> automatic 422 error
  * wrong type?           -> automatic 422 error
  * out-of-range value?   -> automatic 422 error
...all BEFORE your code runs, and all documented in /docs automatically.

For an LLM API this matters: a bad request should be rejected here, cheaply,
instead of being sent to the LLM (which costs money per call).

Run it:
    uvicorn main:app --reload
Then open http://localhost:8000/docs
"""

from pydantic import BaseModel, Field
from fastapi import FastAPI

app = FastAPI(title="Lesson 3 — Validation")


# A Pydantic model = the contract for the request body.
# FastAPI reads this and validates every incoming request against it.
class ChatRequest(BaseModel):
    # `message` is required, must be a string, 1-2000 chars.
    message: str = Field(
        ...,  # the ... means "required, no default"
        min_length=1,
        max_length=20,
        description="What the user wants to say to the model.",
    )
    # `model` is optional — it has a default, so clients can omit it.
    model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Which model to use.",
    )
    # `temperature` must be between 0 and 1 if provided.
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


# You can also validate the RESPONSE shape. `response_model` guarantees the
# output matches this structure (and documents it).
class ChatResponse(BaseModel):
    reply: str
    model_used: str


@app.post("/chat", response_model=ChatResponse) # Whatever this function returns must match the ChatResponse shape.
#" It's a promise about the output — FastAPI checks it"
def chat(req: ChatRequest): # "The caller must send me data that matches the ChatRequest form."
    # By the time we get here, req is GUARANTEED valid:
    #   req.message is a non-empty string <= 2000 chars
    #   req.temperature is a float in [0, 1]
    # We wrote zero validation code to get that.
    fake_reply = f"You said: {req.message!r} (temp={req.temperature})"
    return ChatResponse(reply=fake_reply, model_used=req.model)
