"""
LESSON 4 — Putting it all together (CAPSTONE)
=============================================

This combines the three ideas from lessons 1-3 into one realistic system:

  1. SUPERVISOR + ROUTING (lesson 1): a team lead decides who works next.
  2. SUBGRAPH AS A REUSABLE AGENT (lesson 2): the "research" worker is itself
     a small multi-step graph, dropped in as a single node.
  3. PARALLEL EXECUTION (lesson 3): inside the research agent, three sources
     are gathered at the same time.

SCENARIO: produce a briefing document.
  supervisor ─► research_agent (subgraph, runs 3 sources in parallel)
             ─► writer
             ─► reviewer
             ─► FINISH

Still no LLM here (see lesson 5 for the LLM supervisor) so you can run it and
watch the control flow with zero setup.

Run it:  python lesson_04_full_system.py
"""

from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# STATE — one shared whiteboard for the whole system
# ---------------------------------------------------------------------------
class BriefingState(TypedDict):
    task: str
    findings: Annotated[list[str], operator.add]   # written in parallel -> reducer
    log: Annotated[list[str], operator.add]
    draft: str
    next: str


# ===========================================================================
# PART A — the research agent, built as a REUSABLE SUBGRAPH with PARALLELISM
# ===========================================================================
def research_dispatch(state: BriefingState) -> dict:
    print("  [research/dispatch] gathering 3 sources in parallel")
    return {}


def source_web(state: BriefingState) -> dict:
    return {"findings": ["web: 3 articles found"]}


def source_data(state: BriefingState) -> dict:
    return {"findings": ["data: 1 dataset found"]}


def source_experts(state: BriefingState) -> dict:
    return {"findings": ["experts: 2 quotes collected"]}


def research_combine(state: BriefingState) -> dict:
    print(f"  [research/combine] merged {len(state['findings'])} sources")
    return {"log": ["research_agent: completed"]}


def build_research_agent():
    """A self-contained research agent (subgraph) that fans out to 3 sources."""
    g = StateGraph(BriefingState)
    g.add_node("dispatch", research_dispatch)
    g.add_node("web", source_web)
    g.add_node("data", source_data)
    g.add_node("experts", source_experts)
    g.add_node("combine", research_combine)

    g.add_edge(START, "dispatch")
    # fan-out
    g.add_edge("dispatch", "web")
    g.add_edge("dispatch", "data")
    g.add_edge("dispatch", "experts")
    # fan-in
    g.add_edge("web", "combine")
    g.add_edge("data", "combine")
    g.add_edge("experts", "combine")
    g.add_edge("combine", END)
    return g.compile()


# ===========================================================================
# PART B — the supervisor and the other workers (lesson 1 pattern)
# ===========================================================================
def supervisor(state: BriefingState) -> dict:
    log = state["log"]
    if not any("research_agent" in s for s in log):
        decision = "research_agent"
    elif not any("writer" in s for s in log):
        decision = "writer"
    elif not any("reviewer" in s for s in log):
        decision = "reviewer"
    else:
        decision = "FINISH"
    print(f"[supervisor] next -> {decision}")
    return {"next": decision}


def writer(state: BriefingState) -> dict:
    print("  [writer] writing briefing from findings")
    draft = "BRIEFING: " + "; ".join(state["findings"])
    return {"draft": draft, "log": ["writer: draft ready"]}


def reviewer(state: BriefingState) -> dict:
    print("  [reviewer] approving briefing")
    return {"log": ["reviewer: approved"]}


def route(state: BriefingState) -> str:
    return END if state["next"] == "FINISH" else state["next"]


# ===========================================================================
# PART C — assemble the top-level graph
# ===========================================================================
def build_system():
    system = StateGraph(BriefingState)

    # The research agent subgraph is added as ONE node here.
    system.add_node("research_agent", build_research_agent())
    system.add_node("supervisor", supervisor)
    system.add_node("writer", writer)
    system.add_node("reviewer", reviewer)

    system.add_edge(START, "supervisor")
    system.add_conditional_edges(
        "supervisor",
        route,
        {
            "research_agent": "research_agent",
            "writer": "writer",
            "reviewer": "reviewer",
            END: END,
        },
    )
    # every worker reports back to the supervisor (the supervisor loop)
    system.add_edge("research_agent", "supervisor")
    system.add_edge("writer", "supervisor")
    system.add_edge("reviewer", "supervisor")

    return system.compile()


if __name__ == "__main__":
    app = build_system()
    result = app.invoke(
        {"task": "Create a briefing on renewable energy", "findings": [], "log": [], "draft": "", "next": ""}
    )

    print("\n=== DRAFT ===")
    print(result["draft"])
    print("\n=== LOG ===")
    for line in result["log"]:
        print(" -", line)
