"""
STEP 3 — The supervisor: one user request -> one trace across every hop
=======================================================================

User asks:  "Plan my trip to Paris, my budget is 500 USD"

    STEP 1  DISCOVER  read the Agent Cards and find who has the skills we need
    STEP 2  DELEGATE  ask BOTH agents at the same time over A2A
                        Weather Agent  -> "What's the weather in Paris?"
                        Currency Agent -> "Convert 500 USD to EUR"
    STEP 3  ANSWER    combine the two replies, print the trace ID

The supervisor STARTS the trace (the root span). Every A2A request carries
the trace ID in `metadata.traceparent`, so the agents and the MCP tools all
add their spans to this same trace.

Run (terminal 3):
    python observability_lab/03_supervisor.py                  # Paris, 500 USD -> EUR
    python observability_lab/03_supervisor.py Tokyo 300 JPY    # your own trip
    python observability_lab/03_supervisor.py Atlantis         # a tool FAILS: see the red span
Then:
    python observability_lab/04_view_trace.py
"""

# Import telemetry FIRST: it configures tracing before the A2A SDK loads.
from telemetry import SpanKind, inject_trace, setup_tracing

import asyncio
import sys

import httpx

from a2a.client import A2ACardResolver, AgentCardResolutionError, ClientConfig, create_client
from a2a.helpers import get_message_text, new_text_message
from a2a.types import AgentCard, Role, SendMessageRequest

tracer = setup_tracing("supervisor")

AGENT_URLS = ["http://127.0.0.1:9201", "http://127.0.0.1:9202"]


# ---------------------------------------------------------------------------
# STEP 1 — discover agents from their cards, indexed by skill id
# ---------------------------------------------------------------------------
async def discover_agents() -> dict[str, AgentCard]:
    with tracer.start_as_current_span("discover agents") as span:
        by_skill: dict[str, AgentCard] = {}
        async with httpx.AsyncClient() as http:
            for url in AGENT_URLS:
                try:
                    card = await A2ACardResolver(http, url).get_agent_card()
                except AgentCardResolutionError:
                    print(f"  (no agent at {url})")
                    continue
                for skill in card.skills:
                    by_skill[skill.id] = card
        span.set_attribute("agents.found", sorted({c.name for c in by_skill.values()}))
        return by_skill


# ---------------------------------------------------------------------------
# STEP 2 — send one A2A message, with our trace ID in the request metadata
# ---------------------------------------------------------------------------
async def ask_agent(card: AgentCard, question: str) -> str:
    with tracer.start_as_current_span(
        f"a2a SendMessage -> {card.name}", kind=SpanKind.CLIENT,
        attributes={"a2a.agent": card.name, "a2a.url": card.supported_interfaces[0].url,
                    "a2a.input": question},
    ) as span:
        request = SendMessageRequest(message=new_text_message(question, role=Role.ROLE_USER))
        # >>> the key line: our trace ID rides along inside the A2A request <<<
        request.metadata.update(inject_trace())

        client = await create_client(card, client_config=ClientConfig(streaming=False))
        async with client:
            async for response in client.send_message(request):
                answer = get_message_text(response.message)
                span.set_attribute("a2a.output", answer)
                return answer
    return "(no reply)"


async def main(city: str, amount: str, currency: str) -> None:
    user_request = f"Plan my trip to {city}, my budget is {amount} USD"

    # The ROOT span: everything below becomes part of this one trace.
    with tracer.start_as_current_span("plan trip", attributes={"user.request": user_request}) as root:
        trace_id = format(root.get_span_context().trace_id, "032x")
        print(f"User: {user_request}")
        print(f"Trace ID: {trace_id}\n")

        print("STEP 1 · discovering agents...")
        agents = await discover_agents()
        for skill_id, card in agents.items():
            print(f"  skill {skill_id:<17} -> {card.name}")

        print("\nSTEP 2 · asking both agents in parallel over A2A...")
        weather, money = await asyncio.gather(
            ask_agent(agents["get_weather"], f"What's the weather in {city}?"),
            ask_agent(agents["convert_currency"], f"Convert {amount} USD to {currency}"),
        )

        print("\nSTEP 3 · answer:")
        print(f"  {weather}")
        print(f"  Budget: {money}")

    print("\nNow see the whole journey:  python observability_lab/04_view_trace.py")


if __name__ == "__main__":
    args = sys.argv[1:]
    city = args[0] if len(args) > 0 else "Paris"
    amount = args[1] if len(args) > 1 else "500"
    currency = args[2] if len(args) > 2 else "EUR"
    asyncio.run(main(city, amount, currency))
