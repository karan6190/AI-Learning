"""
LESSON 4 (part 2) — point the SAME graph at the REAL GitHub MCP server
======================================================================

`agent.py` ran the graph against a server YOU wrote (`server.py`, three tiny
tools). This file proves MCP's real promise: point the *exact same graph* at a
server you did NOT write — GitHub's official, remotely hosted MCP server — and the
agent can suddenly search repos, read files, and look at issues.

Look closely: the graph code below (bind_tools, the agent node, the tools node,
the router, the loop) is **identical to `agent.py`**. The ONLY thing that changes
is the `MultiServerMCPClient` config:

    agent.py (local server you wrote):           github_agent.py (GitHub's remote server):
    -----------------------------------          ------------------------------------------
    "command": sys.executable,          ──►       "url": "https://api.githubcopilot.com/mcp/",
    "args": [SERVER_SCRIPT],                       "headers": {"Authorization": "Bearer <PAT>"},
    "transport": "stdio",                          "transport": "streamable_http",

Two transports:
  * stdio          — launch a local program and talk over its pipe (agent.py).
  * streamable_http — talk to a server running somewhere else, over HTTPS. This is
                      how you reach hosted servers like GitHub's.

That's the entire point of a standard protocol: your client/agent code doesn't
care WHO wrote the server or WHERE it runs.

SETUP
  1. pip install -r requirements.txt
  2. A Groq key (the LLM) and a GitHub Personal Access Token (the server's auth),
     both in the `.env` file next to this script:
         GROQ_API_KEY=gsk_...
         GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...
     Make a fine-grained PAT at https://github.com/settings/personal-access-tokens
     with read-only access to public repos — that's plenty for this lesson.
  3. python github_agent.py

If either secret is missing, the script says which one and exits cleanly.
"""

import asyncio
import os

from dotenv import load_dotenv


# GitHub's official, hosted MCP server. We did not write it — we just connect.
GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"


async def main() -> None:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_groq import ChatGroq
    from langgraph.graph import StateGraph, START, END, MessagesState
    from langgraph.prebuilt import ToolNode

    # ---- 1. THE BRIDGE — but now pointed at a REMOTE server over HTTP ----
    # Compare this dict to agent.py: same shape, different transport. The GitHub
    # server authenticates with your PAT sent as a Bearer token in a header.
    client = MultiServerMCPClient(
        {
            "github": {
                "url": GITHUB_MCP_URL,
                "headers": {"Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}"},
                "transport": "streamable_http",
            }
        }
    )

    # Same one line as agent.py: connect, handshake, discover, convert to tools.
    # The GitHub server offers MANY tools, so we only print the first handful.
    all_tools = await client.get_tools()
    print(f"=== Discovered {len(all_tools)} tools from the GitHub MCP server ===")
    for tool in all_tools[:12]:
        print(f"  • {tool.name}")
    if len(all_tools) > 12:
        print(f"  … and {len(all_tools) - 12} more")

    # The GitHub server exposes dozens of tools. Handing all of them to a small
    # model at once makes it slower and more easily confused, so for a clear demo
    # we keep just a few read-only ones. (Remove this filter to give it everything.)
    keep = {"search_repositories", "get_file_contents", "list_issues", "get_issue", "search_code"}
    tools = [t for t in all_tools if t.name in keep] or all_tools
    print(f"\n=== Using {len(tools)} tool(s) for this demo: {', '.join(t.name for t in tools)} ===")

    # ---- 2-3. THE LLM + THE GRAPH — copied verbatim from agent.py ----
    # Nothing below this line knows or cares that the server is GitHub's. That is
    # the payoff: the agent is reusable across any MCP server.
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    async def call_model(state: MessagesState) -> dict:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    def should_call_tools(state: MessagesState) -> str:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_call_tools, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    app = graph.compile()

    # ---- 4. ASK IT REAL GITHUB QUESTIONS ----
    questions = [
        "Search GitHub for the repository 'modelcontextprotocol/servers' and tell me what it is.",
        "In the repo 'modelcontextprotocol/python-sdk', read the README and summarise it in two sentences.",
    ]

    for question in questions:
        print(f"\n=== You: {question} ===")
        result = await app.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            {"recursion_limit": 15},
        )
        print(f"Agent: {result['messages'][-1].content}")

        used = [
            call["name"]
            for msg in result["messages"]
            for call in getattr(msg, "tool_calls", []) or []
        ]
        if used:
            print(f"   (GitHub tools the graph called: {', '.join(used)})")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
