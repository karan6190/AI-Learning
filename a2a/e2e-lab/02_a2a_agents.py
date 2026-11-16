"""
STEP 2 — Two A2A agents that use MCP tools
==========================================

    Weather Agent    http://127.0.0.1:9201   uses MCP tool  get_weather
    Currency Agent   http://127.0.0.1:9202   uses MCP tool  convert_currency

Each agent is:
    * an A2A SERVER  (other agents send it tasks; same 3 pieces as lab/02_basic_agents.py)
    * an MCP CLIENT  (it calls tools on the MCP server from step 1)

Tracing, at each agent:

    A2A request arrives ── metadata.traceparent ──► continue_trace("agent ...")
                                                          │
                                                          ├─ span "mcp call_tool ..."
                                                          │     sends _meta.traceparent ──► MCP server
                                                          ▼
                                                    reply goes back over A2A

Run it (terminal 2):   python observability_lab/02_a2a_agents.py
Needs:                 01_mcp_server.py already running
"""

# Import telemetry FIRST: it configures tracing before the A2A SDK loads.
from telemetry import SpanKind, continue_trace, inject_trace, mark_error, setup_tracing, short_id

import asyncio
import re

import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from starlette.applications import Starlette

from a2a.helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, UnsupportedOperationError

tracer = setup_tracing("a2a-agents")

HOST = "127.0.0.1"
RPC_PATH = "/a2a/jsonrpc"
MCP_URL = "http://127.0.0.1:9100/mcp"


# ===========================================================================
# The MCP CLIENT part: call one tool, and pass our trace ID along in `_meta`
# ===========================================================================
async def call_mcp_tool(tool: str, arguments: dict) -> str:
    with tracer.start_as_current_span(
        f"mcp call_tool {tool}", kind=SpanKind.CLIENT,
        attributes={"mcp.tool.name": tool, "mcp.server.url": MCP_URL},
    ) as span:
        async with streamablehttp_client(MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Opening a session has a cost. Its own span makes that cost visible.
                with tracer.start_as_current_span("mcp initialize session"):
                    await session.initialize()
                # >>> the key line: our trace ID rides along inside the MCP request <<<
                result = await session.call_tool(tool, arguments, meta=inject_trace())

        text = result.content[0].text if result.content else ""
        if result.isError:                       # the tool failed (MCP's isError flag)
            mark_error(span, text)
            return f"(tool error: {text})"
        return text


# ===========================================================================
# The agents' "brains": read the question, pick arguments, call the MCP tool
# ===========================================================================
async def weather_brain(question: str) -> str:
    match = re.search(r"\bin\s+([A-Za-z ]+?)(?:[?.!,]|$)", question)
    city = match.group(1).strip().title() if match else "Paris"
    return f"Weather in {city}: {await call_mcp_tool('get_weather', {'city': city})}"


async def currency_brain(question: str) -> str:
    match = re.search(r"(\d+(?:\.\d+)?)\s*([A-Za-z]{3})\s+(?:to|in)\s+([A-Za-z]{3})", question)
    if not match:
        return "Please ask like: 'convert 500 USD to EUR'."
    amount, src, dst = float(match.group(1)), match.group(2).upper(), match.group(3).upper()
    return await call_mcp_tool("convert_currency", {"amount": amount, "from_ccy": src, "to_ccy": dst})


# ===========================================================================
# The A2A SERVER part (same as lab/02_basic_agents.py, plus continue_trace)
# ===========================================================================
class TracedExecutor(AgentExecutor):
    def __init__(self, name: str, brain):
        self.name = name
        self.brain = brain

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        question = context.get_user_input()
        # The supervisor put its traceparent in the A2A request's metadata.
        # continue_trace() picks it up, so our span joins the SAME trace.
        with continue_trace(tracer, context.metadata, f"agent {self.name}",
                            **{"a2a.agent": self.name, "a2a.input": question}) as span:
            answer = await self.brain(question)
            span.set_attribute("a2a.output", answer)
            print(f"[trace {short_id()}] [{self.name}] {question!r} -> {answer!r}")
        await event_queue.enqueue_event(new_text_message(answer, context_id=context.context_id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError()


def make_card(name: str, description: str, port: int, skill: AgentSkill) -> AgentCard:
    return AgentCard(
        name=name, description=description, version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://{HOST}:{port}{RPC_PATH}",
                                             protocol_binding="JSONRPC", protocol_version="1.0")],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        skills=[skill],
    )


AGENTS = [
    (make_card("Weather Agent", "Reports today's weather for a city.", 9201,
               AgentSkill(id="get_weather", name="Get weather",
                          description="Tells you today's weather in the city you name.",
                          tags=["weather"], examples=["What's the weather in Paris?"])),
     weather_brain, 9201),
    (make_card("Currency Agent", "Converts money between currencies.", 9202,
               AgentSkill(id="convert_currency", name="Convert currency",
                          description="Converts an amount, e.g. 'convert 500 USD to EUR'.",
                          tags=["currency", "convert"], examples=["Convert 500 USD to EUR"])),
     currency_brain, 9202),
]


def make_app(card: AgentCard, brain) -> Starlette:
    handler = DefaultRequestHandler(agent_executor=TracedExecutor(card.name, brain),
                                    task_store=InMemoryTaskStore(), agent_card=card)
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url=RPC_PATH)
    return Starlette(routes=routes)


async def main() -> None:
    servers = []
    for card, brain, port in AGENTS:
        print(f"{card.name:<15} card: http://{HOST}:{port}/.well-known/agent-card.json")
        config = uvicorn.Config(make_app(card, brain), host=HOST, port=port, log_level="warning")
        servers.append(uvicorn.Server(config))
    print(f"\nAgents running (using MCP tools at {MCP_URL}). Press Ctrl+C to stop.\n")
    await asyncio.gather(*(s.serve() for s in servers))


if __name__ == "__main__":
    asyncio.run(main())
