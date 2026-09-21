"""
LESSON 3 — Parallel execution (fan-out / fan-in)
=================================================

BIG IDEA
--------
Sometimes several agents can work AT THE SAME TIME because they don't depend on
each other. Example: to research a company you could, in parallel, look at its
(a) finances, (b) news, and (c) competitors. Doing these three at once is faster
than one-after-another.

    dispatch ─┬─► finance_agent  ─┐
              ├─► news_agent     ─┼─► combine ─► END
              └─► competitor_agent┘

- "FAN-OUT": one node points to MANY nodes. LangGraph runs them in parallel.
- "FAN-IN": many nodes point to ONE node. That node waits for ALL of them,
  then runs once.

THE ONE GOTCHA — reducers
-------------------------
When parallel nodes all write to the SAME state field, LangGraph must merge
their writes. You tell it HOW to merge using a "reducer". For a list, the
reducer `operator.add` concatenates them. WITHOUT a reducer, two parallel writes
to the same key would collide and LangGraph raises an error. This is the single
most common mistake beginners hit with parallel graphs.

Run it:  python lesson_03_parallel_execution.py
"""

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
class ResearchState(TypedDict):
    company: str
    # `findings` is written by THREE parallel nodes, so it MUST have a reducer.
    findings: Annotated[list[str], operator.add]
    report: str


# ---------------------------------------------------------------------------
# NODES
# ---------------------------------------------------------------------------
def dispatch(state: ResearchState) -> dict:
    # This node just kicks things off. The parallelism comes from the EDGES
    # we draw below, not from anything special inside this function.
    print(f"[dispatch] researching '{state['company']}' from 3 angles at once")
    return {}


def finance_agent(state: ResearchState) -> dict:
    print("  [finance] analysing revenue and profit")
    return {"findings": ["finance: revenue up 12% year over year"]}


def news_agent(state: ResearchState) -> dict:
    print("  [news] scanning recent headlines")
    return {"findings": ["news: launched a new product line last month"]}


def competitor_agent(state: ResearchState) -> dict:
    print("  [competitor] mapping rivals")
    return {"findings": ["competitor: 2 major rivals, both smaller"]}


def combine(state: ResearchState) -> dict:
    # This is the FAN-IN node. LangGraph only runs it AFTER all three parallel
    # agents have finished. By now, `findings` holds all three lists merged.
    print("[combine] all agents done -> merging into one report")
    report = " | ".join(state["findings"])
    return {"report": report}


# ---------------------------------------------------------------------------
# BUILD THE GRAPH
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("dispatch", dispatch)
    graph.add_node("finance", finance_agent)
    graph.add_node("news", news_agent)
    graph.add_node("competitor", competitor_agent)
    graph.add_node("combine", combine)

    graph.add_edge(START, "dispatch")

    # FAN-OUT: dispatch -> all three agents. Because these three edges leave the
    # same node, LangGraph schedules the three agents to run in parallel.
    graph.add_edge("dispatch", "finance")
    graph.add_edge("dispatch", "news")
    graph.add_edge("dispatch", "competitor")

    # FAN-IN: all three agents -> combine. `combine` waits for all three.
    graph.add_edge("finance", "combine")
    graph.add_edge("news", "combine")
    graph.add_edge("competitor", "combine")

    graph.add_edge("combine", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# RUN IT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"company": "Acme Corp", "findings": [], "report": ""})

    print("\n=== FINAL REPORT ===")
    print(result["report"])
