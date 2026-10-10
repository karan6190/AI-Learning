# Lesson 1 — Hello, API!

**Goal:** run your very first API and meet the free interactive docs page.

## The idea

An API is a set of **endpoints** (URLs) that return data. Here we make one endpoint at `/`
that returns a small JSON message. That's a complete, working API.

## Run it

```bash
uvicorn main:app --reload
```

You should see `Uvicorn running on http://127.0.0.1:8000`.

## Try it — three ways

**1. In your browser:** open <http://localhost:8000> — you'll see the JSON response.

**2. The interactive docs (the FastAPI "wow"):** open <http://localhost:8000/docs>
You get a clickable page listing every endpoint. Click `GET /`, press **Try it out** →
**Execute**, and see the live response. *You wrote zero lines of docs code — FastAPI
generated this from your functions.*

**3. From the command line** (optional):
```bash
curl http://localhost:8000/hello
```

## What to notice

- `app = FastAPI()` creates the whole API.
- `@app.get("/")` is a **decorator** — it attaches the function below to the URL `/` for GET requests.
- Returning a Python `dict` → FastAPI sends it back as **JSON** automatically.
- The `/docs` page came for free.

## Line-by-line

| Code | Meaning |
|------|---------|
| `app = FastAPI(...)` | create the application object Uvicorn will run |
| `@app.get("/")` | "run this function for GET requests to `/`" |
| `return {...}` | the dict becomes the JSON response body |

## Things to try

1. Change the message text, save, and refresh — `--reload` picks it up instantly.
2. Add a third endpoint `/time` that returns the current time
   (`from datetime import datetime; return {"now": datetime.now().isoformat()}`).
3. Visit <http://localhost:8000/redoc> — a second, different docs style, also free.

## Next

Lesson 2 adds the HTTP vocabulary: GET vs POST, path params, query params, status codes.
