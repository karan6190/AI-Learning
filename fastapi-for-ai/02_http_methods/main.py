"""
Lesson 2 — HTTP methods, path params, query params, status codes.

This lesson keeps a tiny in-memory list of "messages" and shows the four core
HTTP ideas you'll use constantly:

  * GET    -> read data
  * POST   -> create data
  * DELETE -> remove data
  * path params ( /messages/{id} ) and query params ( ?limit=5 )
  * status codes (200, 201, 404)

Run it:
    uvicorn main:app --reload
Then open http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, status

app = FastAPI(title="Lesson 2 — HTTP methods")

# A fake "database": just a Python list that lives in memory.
# It resets every time the server restarts. Good enough to learn with.
messages: list[dict] = [
    {"id": 1, "text": "Hello"},
    {"id": 2, "text": "World"},
]


# ---- GET: read a collection -------------------------------------------------
# `limit` is a QUERY parameter: /messages?limit=1
# FastAPI reads it from the URL, converts it to int, and defaults it to 10.
@app.get("/messages")
def list_messages(limit: int = 10):
    return messages[:limit]


# ---- GET: read one item -----------------------------------------------------
# `message_id` is a PATH parameter: it's part of the URL itself, /messages/2
@app.get("/messages/{message_id}")
def get_message(message_id: int):
    for msg in messages:
        if msg["id"] == message_id:
            return msg
    # Not found -> raise a 404 with a clear message instead of returning null.
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No message with id {message_id}",
    )


# ---- POST: create an item ---------------------------------------------------
# `text` here comes from the request body. (In the next lesson we'll do this
# properly with Pydantic — for now FastAPI treats it as a simple body field.)
# status_code=201 is the convention for "created something new".
@app.post("/messages", status_code=status.HTTP_201_CREATED)
def create_message(text: str):
    new_id = max((m["id"] for m in messages), default=0) + 1
    new_message = {"id": new_id, "text": text}
    messages.append(new_message)
    return new_message


# ---- DELETE: remove an item -------------------------------------------------
@app.delete("/messages/{message_id}")
def delete_message(message_id: int):
    for i, msg in enumerate(messages):
        if msg["id"] == message_id:
            messages.pop(i)
            return {"deleted": message_id}
    raise HTTPException(status_code=404, detail=f"No message with id {message_id}")
