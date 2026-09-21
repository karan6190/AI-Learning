"""
LESSON 2 — A subgraph as a reusable agent component
====================================================

BIG IDEA
--------
A single node is fine for tiny work. But a real "agent" usually has several
internal steps: think -> act -> check. Instead of cramming that into one node,
we build the agent as its OWN small graph (a "subgraph") and then plug that
whole graph into a bigger graph AS IF it were a single node.

    Outer graph:   START ─► research_agent ─► END
                                 │
                                 ▼  (research_agent is actually...)
    Inner graph:   START ─► plan ─► search ─► summarise ─► END

WHY THIS MATTERS
- Reusability: build the agent once, drop it into many systems.
- Encapsulation: the outer graph doesn't care HOW the agent works internally.
- Testability: you can run and test the subgraph on its own.

The trick: a compiled LangGraph is "runnable", and any runnable can be used as
a node. So `outer.add_node("research_agent", inner_compiled_graph)` just works —
as long as the inner and outer graphs share the same state fields they read/write.

Run it:  python lesson_02_subgraph_agent.py
"""

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# SHARED STATE
# ---------------------------------------------------------------------------
# For a subgraph to slot into an outer graph cleanly, the fields it reads and
# writes should exist in the outer state too. Here we keep ONE state shape and
# reuse it for both graphs — the simplest, most beginner-friendly approach.
class State(TypedDict):
    topic: str
    notes: Annotated[list[str], operator.add]
    summary: str


# ---------------------------------------------------------------------------
# 1. BUILD THE AGENT AS A SUBGRAPH
# ---------------------------------------------------------------------------
# This "research agent" internally does three steps. Each is a normal node.
def plan(state: State) -> dict:
    print("    [research-agent/plan] deciding what to look up")
    return {"notes": [f"plan: research the topic '{state['topic']}'"]}


def search(state: State) -> dict:
    print("    [research-agent/search] looking things up")
    return {"notes": ["search: found source A and source B"]}


def summarise(state: State) -> dict:
    print("    [research-agent/summarise] condensing findings")
    return {"summary": f"A short summary about {state['topic']} based on 2 sources."}


def build_research_agent():
    """Build and compile the research agent as its own standalone graph."""
    sub = StateGraph(State)
    sub.add_node("plan", plan)
    sub.add_node("search", search)
    sub.add_node("summarise", summarise)

    sub.add_edge(START, "plan")
    sub.add_edge("plan", "search")
    sub.add_edge("search", "summarise")
    sub.add_edge("summarise", END)

    return sub.compile()   # <-- a compiled graph is reusable as a single node


# ---------------------------------------------------------------------------
# 2. USE THE SUBGRAPH INSIDE A BIGGER GRAPH
# ---------------------------------------------------------------------------
def announce(state: State) -> dict:
    print(f"  [outer/announce] final summary: {state['summary']}")
    return {}


def build_outer_graph():
    research_agent = build_research_agent()   # the whole subgraph...

    outer = StateGraph(State)
    # ...added as if it were ONE node. This is the reusable-component pattern.
    outer.add_node("research_agent", research_agent)
    outer.add_node("announce", announce)

    outer.add_edge(START, "research_agent")
    outer.add_edge("research_agent", "announce")
    outer.add_edge("announce", END)

    return outer.compile()


# ---------------------------------------------------------------------------
# 3. RUN IT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # First, prove the agent works ON ITS OWN (great for testing components).
    print("=== Running the research agent BY ITSELF ===")
    agent = build_research_agent()
    solo = agent.invoke({"topic": "honey production", "notes": [], "summary": ""})
    print("solo summary:", solo["summary"])

    # Now use the SAME agent embedded inside a larger graph.
    print("\n=== Running the OUTER graph (agent embedded as a node) ===")
    app = build_outer_graph()
    result = app.invoke({"topic": "honey production", "notes": [], "summary": ""})

    print("\n=== NOTES COLLECTED ===")
    for n in result["notes"]:
        print(" -", n)
