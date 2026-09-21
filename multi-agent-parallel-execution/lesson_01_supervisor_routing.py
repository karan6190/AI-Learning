"""
LESSON 1 — The Supervisor node and routing logic
==================================================

BIG IDEA
--------
In a multi-agent system, ONE node (the "supervisor") acts like a team lead.
It looks at the current situation and decides "who should work next?".
Every worker reports back to the supervisor, and the supervisor decides again.
This loop continues until the supervisor says "we're done" (FINISH).

    START ─► supervisor ─► worker ─► supervisor ─► ... ─► END

This lesson uses NO large language model on purpose. We route with simple
keyword rules so you can SEE the graph mechanics clearly. In lesson 4 we swap
the rule-based supervisor for an LLM-based one — the graph shape stays the same.

Run it:  python lesson_01_supervisor_routing.py
"""

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# 1. THE STATE
# ---------------------------------------------------------------------------
# The state is the shared "whiteboard" that every node reads from and writes to.
# LangGraph passes this object from node to node.
class TeamState(TypedDict):
    task: str                                  # the original request
    # `Annotated[..., operator.add]` means: when a node returns a `log`,
    # ADD it to the existing list instead of overwriting it. This is called a
    # "reducer". Without it, each node would erase the previous node's writes.
    log: Annotated[list[str], operator.add]
    next: str                                  # which worker the supervisor picked


# ---------------------------------------------------------------------------
# 2. THE SUPERVISOR NODE (the routing brain)
# ---------------------------------------------------------------------------
# The supervisor's ONLY job is to decide who works next. It writes its decision
# into state["next"]. It does NOT do the actual work.
WORKERS = ["researcher", "writer", "reviewer"]


def supervisor(state: TeamState) -> dict:
    task = state["task"].lower()
    done_steps = state["log"]

    # Very simple routing rules. Read them top-to-bottom like a checklist:
    if not any("researcher" in step for step in done_steps):
        decision = "researcher"            # nobody has researched yet
    elif not any("writer" in step for step in done_steps):
        decision = "writer"                # research done, now write
    elif not any("reviewer" in step for step in done_steps):
        decision = "reviewer"              # written, now review
    else:
        decision = "FINISH"                # everyone has had a turn

    print(f"[supervisor] task='{state['task']}' -> next = {decision}")
    return {"next": decision, "log": [f"supervisor routed to {decision}"]}


# ---------------------------------------------------------------------------
# 3. THE WORKER NODES (they do the actual work)
# ---------------------------------------------------------------------------
# Each worker does a small piece of work and writes a line to the log.
# Notice each worker ALWAYS returns control — it never decides who is next.
def researcher(state: TeamState) -> dict:
    print("  [researcher] gathering facts...")
    return {"log": ["researcher: found 3 relevant facts"]}


def writer(state: TeamState) -> dict:
    print("  [writer] drafting content...")
    return {"log": ["writer: wrote a first draft"]}


def reviewer(state: TeamState) -> dict:
    print("  [reviewer] checking quality...")
    return {"log": ["reviewer: approved the draft"]}


# ---------------------------------------------------------------------------
# 4. THE ROUTING FUNCTION
# ---------------------------------------------------------------------------
# After the supervisor runs, LangGraph asks this function "where do we go now?".
# It simply reads the decision the supervisor already made and returns an edge
# name. Returning END stops the graph.
def route_from_supervisor(state: TeamState) -> str:
    if state["next"] == "FINISH":
        return END
    return state["next"]


# ---------------------------------------------------------------------------
# 5. BUILD THE GRAPH (wire the nodes together)
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(TeamState)

    # Register every node by name.
    graph.add_node("supervisor", supervisor)
    graph.add_node("researcher", researcher)
    graph.add_node("writer", writer)
    graph.add_node("reviewer", reviewer)

    # The graph always starts at the supervisor.
    graph.add_edge(START, "supervisor")

    # CONDITIONAL edge: after the supervisor, jump to whichever worker
    # `route_from_supervisor` names (or END). The dict maps the function's
    # return value to the actual node name.
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"researcher": "researcher", "writer": "writer", "reviewer": "reviewer", END: END},
    )

    # KEY PATTERN: every worker goes straight BACK to the supervisor.
    # This creates the "supervisor loop" — the supervisor stays in control.
    for worker in WORKERS:
        graph.add_edge(worker, "supervisor")

    return graph.compile()


# ---------------------------------------------------------------------------
# 6. RUN IT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = build_graph()

    result = app.invoke({"task": "Write a short article about bees", "log": []})

    print("\n=== FINAL LOG ===")
    for line in result["log"]:
        print(" -", line)
