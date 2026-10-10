# Lesson 2 — HTTP methods, params, and status codes

**Goal:** learn the vocabulary every web API uses — the verbs, the two kinds of
parameters, and the result codes.

## The idea

Every API request is: a **method** (verb) + an **endpoint** (noun) + maybe some **data**,
and you get back a **status code** + a **body**.

| Method | We use it to | Endpoint in this lesson |
|--------|--------------|-------------------------|
| `GET` | read | `GET /messages`, `GET /messages/2` |
| `POST` | create | `POST /messages` |
| `DELETE` | remove | `DELETE /messages/2` |

Two kinds of parameters:
- **Path parameter** — part of the URL itself: `/messages/{message_id}` → `/messages/2`.
  Use it to identify *which* thing.
- **Query parameter** — after a `?`: `/messages?limit=5`. Use it to filter / tweak.

Status codes you'll meet here: `200` OK, `201` Created, `404` Not Found.

## Run it

```bash
uvicorn main:app --reload
```
Open <http://localhost:8000/docs> and try each endpoint.

## Walk-through

1. `GET /messages?limit=1` → returns just the first message. That `limit` is a query param.
2. `GET /messages/2` → returns message 2. That `2` is a path param.
3. `GET /messages/999` → returns a **404** with a clear error. Try it — see how a good API
   fails *loudly and clearly* rather than returning nothing.
4. `POST /messages` with `text=Howdy` → creates a new message, returns **201**.
5. `DELETE /messages/1` → removes it.

> The "database" is just an in-memory list, so it resets when you restart the server. That's
> fine for learning — real apps swap this for an actual database.

## What to notice

- Function parameters become request inputs automatically. FastAPI reads the type hint
  (`message_id: int`) and converts/validates it — ask for `/messages/abc` and you get a
  clean error, because `abc` isn't an `int`.
- `raise HTTPException(404, ...)` is the right way to say "not found".
- The docs page already shows the status codes and parameters — still free.

## Things to try

1. Add a `PUT /messages/{message_id}` endpoint that updates a message's text.
2. Make `limit` reject values above 100 (peek at Lesson 3 — this is what validation is for).
3. Call `GET /messages/abc` and read the error FastAPI gives you.

## Next

Lesson 3 introduces **Pydantic** — proper request validation, and the clearest answer to
"why not just use Flask?"
