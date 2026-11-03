"""
LESSON 4 — LangGraph + MCP, end to end (building the GRAPH by hand)
===================================================================

In Lesson 2 YOU chose which tool to call. Here an LLM does it — but instead of
using a one-line prebuilt agent, we BUILD THE GRAPH OURSELVES so you can see
exactly where and how a tool gets called inside a LangGraph.

The bridge is still one small library: `langchain-mcp-adapters`. It connects to
the MCP server from `server.py`, discovers its tools, and converts each one into
a LangChain tool a LangGraph node can run.

THE GRAPH WE BUILD (a tiny ReAct loop):

        ┌───────┐   has tool calls?   ┌───────┐
   START│ agent │────────── yes ─────►│ tools │
        │ (LLM) │◄───────────────────│ (MCP) │
        └───┬───┘   (result goes back)└───────┘
            │ no (final answer)
            ▼
           END

  * "agent" node = the LLM. Each turn it either answers, or emits a TOOL CALL
    ("call add with a=23, b=19").
  * "tools" node = runs whichever MCP tool the LLM asked for, over the MCP
    protocol, and puts the result back into the conversation.
  * the ROUTER edge looks at the LLM's last message: if it asked for a tool, go
    to "tools"; otherwise we're done -> END.
  * "tools" always loops back to "agent" so the LLM can read the result and
    continue. That loop is what makes it an "agent".

The full stack underneath:

    our graph (agent + tools nodes)
        │  LangChain tools
    langchain-mcp-adapters   <-- the bridge
        │  MCP protocol (stdio)
    server.py (FastMCP: add / multiply / word_count)   <-- unchanged

SETUP (only for this lesson — Lessons 1-4 still need no key)
  1. pip install -r requirements.txt
  2. Put a Groq key in a `.env` file next to this script:
         GROQ_API_KEY=gsk_...your key...
  3. python agent.py

If no key is found, the script explains what to do and exits cleanly.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv


# How to launch the MCP server: run server.py with the SAME python running us.
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")


async def main() -> None:
    # Imports live inside main() so a missing key never triggers heavy imports.
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_groq import ChatGroq
    from langgraph.graph import StateGraph, START, END, MessagesState
    from langgraph.prebuilt import ToolNode

    # ---- 1. THE BRIDGE: connect to the MCP server and discover its tools ----
    # Same "how to launch the server" info as Lesson 2's client, written as config.
    client = MultiServerMCPClient(
        {
            "tools": {
                "command": sys.executable,
                "args": [SERVER_SCRIPT],
                "transport": "stdio",
            }
        }
    )

    # get_tools() connects, does the MCP handshake, lists the tools, and converts
    # each MCP tool into a LangChain tool. One line = all of Lesson 2's client.py.
    tools = await client.get_tools()

    print("=== Tools discovered from the MCP server ===")
    for tool in tools:
        print(f"  • {tool.name}: {tool.description}")

    # ---- 2. THE LLM, TOLD ABOUT THE TOOLS ----
    # gpt-oss open model, served by Groq. `bind_tools` hands the tool schemas to
    # the model so it's ALLOWED to emit tool calls. It doesn't run anything yet —
    # it just lets the LLM say "I'd like to call add(23, 19)".
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # ---- 3. BUILD THE GRAPH BY HAND ----
    # MessagesState is a ready-made state with one field: `messages`, a growing
    # list of chat messages. Each node returns messages to APPEND to it.

    # NODE A — the "agent": call the LLM on the whole conversation so far.
    async def call_model(state: MessagesState) -> dict:
        response = await llm_with_tools.ainvoke(state["messages"])
        # The response may contain tool calls or a final answer — either way we
        # just append it. The ROUTER below decides what that means.
        return {"messages": [response]}

    # NODE B — the "tools": ToolNode is a prebuilt node that reads the tool calls
    # from the last message, runs the matching MCP tool(s), and appends the
    # results. This is the single place where a tool is actually CALLED, and it
    # happens INSIDE the graph.
    tool_node = ToolNode(tools)

    # THE ROUTER — a plain function that looks at the LLM's last message and
    # decides where to go next. This is the "has tool calls?" diamond above.
    def should_call_tools(state: MessagesState) -> str:
        last_message = state["messages"][-1]
        if last_message.tool_calls:          # LLM asked for a tool -> run it
            return "tools"
        return END                           # LLM gave a plain answer -> done

    # Wire the nodes and edges together.
    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")           # always start by asking the LLM
    graph.add_conditional_edges(             # after the LLM: branch on the router
        "agent",
        should_call_tools,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "agent")         # after running a tool, back to the LLM

    app = graph.compile()

    # ---- 4. RUN IT: the graph loops agent -> tools -> agent until it answers ----
    questions = [
        "What is 23 plus 19?",
        "What is 6 times 7?",
        "How many words are in the sentence 'MCP gives agents tools'?",
        "Add 10 and 5, then tell me how many words are in the answer.",
    ]

    for question in questions:
        print(f"\n=== You: {question} ===")
        result = await app.ainvoke({"messages": [{"role": "user", "content": question}]})

        # The graph returns the full message history; the last message is the
        # LLM's final answer. Tool calls happened in the messages before it.
        final = result["messages"][-1].content
        print(f"Agent: {final}")

        # Show which MCP tools the graph ran along the way (nice for teaching).
        used = [
            call["name"]
            for msg in result["messages"]
            for call in getattr(msg, "tool_calls", []) or []
        ]
        if used:
            print(f"   (tools the graph called: {', '.join(used)})")


if __name__ == "__main__":
    load_dotenv()  # read GROQ_API_KEY from a local .env file if present

    if not os.getenv("GROQ_API_KEY"):
        print(
            "No GROQ_API_KEY found.\n"
            "This lesson needs a Groq key (free at https://console.groq.com).\n"
            "Create a `.env` file next to this script with:  GROQ_API_KEY=gsk_...\n"
            "Lessons 1-4 still run with no key at all."
        )
        raise SystemExit(0)

    asyncio.run(main())
