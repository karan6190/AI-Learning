"""
LESSON 5 — Making the supervisor SMART with an LLM (optional)
=============================================================

In lessons 1-4 the supervisor used hand-written `if` rules. That was on purpose:
it let you learn the graph mechanics without any API keys.

In the real world you usually want the supervisor to DECIDE with a language
model, so it can handle open-ended tasks. The beautiful part: the graph shape
does NOT change. We only swap the body of the `supervisor` function.

The reliable way to get a routing decision from an LLM is "structured output":
we hand the model a schema and it must reply with one of our allowed worker
names. No brittle string parsing.

SETUP (only for this lesson)
  1. pip install -r requirements.txt
  2. Create a file named `.env` next to this script containing:
         OPENAI_API_KEY=sk-...your key...
  3. python lesson_05_llm_supervisor.py

If no key is found, the script explains what to do and exits cleanly.
"""

from typing import TypedDict, Annotated, Literal
import operator
import os

from langgraph.graph import StateGraph, START, END


class TeamState(TypedDict):
    task: str
    log: Annotated[list[str], operator.add]
    next: str


WORKERS = ["researcher", "writer", "reviewer"]


# ---------------------------------------------------------------------------
# The LLM-powered supervisor
# ---------------------------------------------------------------------------
def make_supervisor():
    """Returns a supervisor node function that asks an LLM who should work next."""
    from pydantic import BaseModel
    from langchain_openai import ChatOpenAI

    # 1. Define the SHAPE of the decision we want back. `Literal` restricts the
    #    model to exactly these choices — it cannot invent a worker name.
    class Route(BaseModel):
        """Which team member should act next?"""
        next: Literal["researcher", "writer", "reviewer", "FINISH"]

    # 2. `with_structured_output` forces the model's reply into the Route schema.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    router = llm.with_structured_output(Route)

    def supervisor(state: TeamState) -> dict:
        system = (
            "You are a supervisor managing these workers: researcher, writer, "
            "reviewer. Given the task and the work done so far, decide who should "
            "act NEXT. A normal order is researcher -> writer -> reviewer. When all "
            "necessary work is complete, reply with FINISH."
        )
        history = "\n".join(state["log"]) or "(nothing done yet)"
        user = f"Task: {state['task']}\n\nWork done so far:\n{history}"

        decision = router.invoke(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        print(f"[LLM supervisor] -> {decision.next}")
        return {"next": decision.next, "log": [f"supervisor routed to {decision.next}"]}

    return supervisor


# ---------------------------------------------------------------------------
# Workers (kept simple; in a real app each could be its own subgraph/agent)
# ---------------------------------------------------------------------------
def researcher(state: TeamState) -> dict:
    return {"log": ["researcher: gathered background facts"]}


def writer(state: TeamState) -> dict:
    return {"log": ["writer: produced a draft"]}


def reviewer(state: TeamState) -> dict:
    return {"log": ["reviewer: approved the draft"]}


def route(state: TeamState) -> str:
    return END if state["next"] == "FINISH" else state["next"]


def build_graph():
    graph = StateGraph(TeamState)
    graph.add_node("supervisor", make_supervisor())
    graph.add_node("researcher", researcher)
    graph.add_node("writer", writer)
    graph.add_node("reviewer", reviewer)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route,
        {"researcher": "researcher", "writer": "writer", "reviewer": "reviewer", END: END},
    )
    for w in WORKERS:
        graph.add_edge(w, "supervisor")

    # `recursion_limit` is a safety net: if a buggy supervisor loops forever,
    # LangGraph stops after this many steps instead of running up your bill.
    return graph.compile()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()   # read OPENAI_API_KEY from a local .env file if present

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "No OPENAI_API_KEY found.\n"
            "This lesson needs an OpenAI key. Create a `.env` file next to this\n"
            "script with:  OPENAI_API_KEY=sk-...\n"
            "Meanwhile, lessons 1-4 run with no key at all."
        )
        raise SystemExit(0)

    app = build_graph()
    result = app.invoke(
        {"task": "Write a blog post about urban gardening", "log": []},
        {"recursion_limit": 20},
    )

    print("\n=== LOG ===")
    for line in result["log"]:
        print(" -", line)
