# Lesson 3 — Validation with Pydantic

**Goal:** declare the shape of a request once, and let FastAPI enforce it automatically.
This is the clearest answer to *"why FastAPI and not Flask?"*

## The idea

A **Pydantic model** is a Python class that describes what valid data looks like:

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
```

FastAPI reads this and, for every incoming request:
- rejects it with a clear **422** error if a field is missing, the wrong type, or out of range,
- converts types for you,
- documents the whole thing in `/docs`.

**You write zero validation code.** In Flask you'd hand-write all these `if` checks.

## Why this matters for AI

Every call to an LLM **costs money**. You want bad requests (empty message, temperature of
`9`, message a megabyte long) rejected *here* — cheaply, instantly — not forwarded to the
LLM. Validation is your first cost-control and safety layer.

## Run it

```bash
uvicorn main:app --reload
```
Open <http://localhost:8000/docs>.

## Try it — see validation work

Send to `POST /chat`:

**Valid:**
```json
{ "message": "Hello there", "temperature": 0.2 }
```
→ `200`, you get a reply.

**Invalid — empty message:**
```json
{ "message": "" }
```
→ `422`, with a message like *"String should have at least 1 character"*.

**Invalid — temperature too high:**
```json
{ "message": "hi", "temperature": 5 }
```
→ `422`, *"Input should be less than or equal to 1"*.

**Invalid — wrong type:**
```json
{ "message": 123 }
```
→ `422`, *"Input should be a valid string"*.

Notice you never wrote any of those error messages. Pydantic did.

## What to notice

- `Field(...)` — the `...` means **required**.
- `ge` / `le` = "greater/less than or equal". `min_length` / `max_length` for strings.
- `response_model=ChatResponse` validates and documents the **output** too.
- The `/docs` page now shows the exact request schema with every rule.

## Things to try

1. Add a `max_tokens: int = Field(default=1024, ge=1, le=4096)` field.
2. Add a `role` field constrained to specific values using
   `Literal["user", "assistant"]` as the type.
3. Try sending extra fields that aren't in the model — see what happens.

## Next

Lesson 4: `async`/`await` — why slow LLM calls need it, and how FastAPI makes one server
handle many requests at once.
