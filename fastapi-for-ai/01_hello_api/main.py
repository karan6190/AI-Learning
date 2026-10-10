"""
Lesson 1 — Hello, API!

The smallest possible FastAPI app. Three things happen here:
  1. We create the app.
  2. We define a "route" (an endpoint) at the URL "/".
  3. We return some data. FastAPI turns our Python dict into JSON automatically.

Run it:
    uvicorn main:app --reload

Then open http://localhost:8000/docs  -> the interactive docs page.
"""

from fastapi import FastAPI

# `app` is the whole API. Uvicorn looks for this variable (that's the "app"
# in the "main:app" command — file `main`, variable `app`).
app = FastAPI(
    title="Lesson 1 — Hello API",
    description="The smallest possible API.",
)


# @app.get("/") means: "when someone sends a GET request to the URL '/',
# run the function below and send back whatever it returns."
@app.get("/")
def read_root():
    # A plain Python dict. FastAPI converts it to JSON for the response.
    return {"status": "alive", "message": "Your first API is running!"}


# A second endpoint, so you can see more than one route in the docs.
@app.get("/hello")
def say_hello():
    return {"greeting": "Hello, world"}
