"""
LAB 2 — Three basic A2A agents (the "servers")
==============================================

We start three tiny agents, each on its own port, each with its own Agent Card:

    Calculator Agent   http://localhost:9001   adds up the numbers in a sentence
    Weather Agent      http://localhost:9002   reports (made-up) weather for a city
    Joke Agent         http://localhost:9003   tells a joke

The "brains" are plain Python functions on purpose. There is no LLM, so you can
focus on the A2A part: how an agent describes itself and answers requests.

Every agent is built from the same three pieces:

    1. AGENT CARD   — its business card, served at /.well-known/agent-card.json
    2. EXECUTOR     — receives the A2A message, calls the brain, sends a reply
    3. HTTP SERVER  — the SDK's routes (card + JSON-RPC) in a Starlette app

Run it:   python lab/02_basic_agents.py
Check:    open http://localhost:9001/.well-known/agent-card.json
Then:     python lab/03_supervisor.py        (in a second terminal)
"""

import asyncio
import random
import re

import uvicorn
from starlette.applications import Starlette

from a2a.helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, UnsupportedOperationError

HOST = "localhost"
RPC_PATH = "/a2a/jsonrpc"


# ===========================================================================
# The agents' "brains" — plain functions: text in, text out
# ===========================================================================
def calculator_brain(text: str) -> str:
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", text)]
    if not numbers:
        return "I couldn't find any numbers to add."
    total = sum(numbers)
    return f"{' + '.join(f'{n:g}' for n in numbers)} = {total:g}"


def weather_brain(text: str) -> str:
    # Take the word after "in" as the city, e.g. "weather in London?" -> "London"
    match = re.search(r"\bin\s+([A-Za-z]+)", text)
    city = match.group(1).title() if match else "your city"
    return f"It's {random.randint(5, 30)}°C and {random.choice(['sunny', 'cloudy', 'rainy'])} in {city}."


JOKES = [
    "Why did the agent cross the network? To get to the other side of the API.",
    "I asked an AI agent to tell me a joke about UDP. It didn't care if I got it.",
    "Two agents walk into a bar. The first one says: 'Let me check your Agent Card.'",
]


def joke_brain(text: str) -> str:
    return random.choice(JOKES)


# ===========================================================================
# PIECE 1 — the Agent Card: what each agent tells the world about itself
# ===========================================================================
def make_card(name: str, description: str, port: int, skill: AgentSkill) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{port}{RPC_PATH}", protocol_binding="JSONRPC", protocol_version="1.0"),
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[skill],
    )


AGENTS = [
    (
        make_card(
            "Calculator Agent", "Does simple arithmetic.", 9001,
            AgentSkill(
                id="add_numbers", name="Add numbers",
                description="Adds up all the numbers found in your message.",
                tags=["math", "add", "plus", "sum", "calculate"],
                examples=["What is 12 plus 30?"],
            ),
        ),
        calculator_brain,
        9001,
    ),
    (
        make_card(
            "Weather Agent", "Reports the current weather for a city.", 9002,
            AgentSkill(
                id="get_weather", name="Get weather",
                description="Tells you the weather in the city you name.",
                tags=["weather", "temperature", "forecast", "rain", "sunny"],
                examples=["What's the weather in London?"],
            ),
        ),
        weather_brain,
        9002,
    ),
    (
        make_card(
            "Joke Agent", "Tells programming jokes.", 9003,
            AgentSkill(
                id="tell_joke", name="Tell a joke",
                description="Tells a short, clean programming joke.",
                tags=["joke", "funny", "laugh", "humor"],
                examples=["Tell me a joke"],
            ),
        ),
        joke_brain,
        9003,
    ),
]


# ===========================================================================
# PIECE 2 — the Executor: A2A message in -> brain -> A2A message out
#   One class works for all three agents; we just hand it a different brain.
# ===========================================================================
class SimpleExecutor(AgentExecutor):
    def __init__(self, name: str, brain):
        self.name = name
        self.brain = brain

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        question = context.get_user_input()          # the text the client sent
        answer = self.brain(question)                # do the work
        print(f"[{self.name}] {question!r} -> {answer!r}")
        # A quick job needs no Task: reply with a single Message and we're done.
        await event_queue.enqueue_event(new_text_message(answer, context_id=context.context_id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError()            # replies are instant; nothing to cancel


# ===========================================================================
# PIECE 3 — the HTTP server for one agent
# ===========================================================================
def make_app(card: AgentCard, brain) -> Starlette:
    handler = DefaultRequestHandler(
        agent_executor=SimpleExecutor(card.name, brain),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url=RPC_PATH)
    return Starlette(routes=routes)


async def main() -> None:
    servers = []
    for card, brain, port in AGENTS:
        print(f"{card.name:<17} card: http://{HOST}:{port}/.well-known/agent-card.json")
        config = uvicorn.Config(make_app(card, brain), host=HOST, port=port, log_level="warning")
        servers.append(uvicorn.Server(config))
    print("\nAll agents running. Press Ctrl+C to stop.\n")
    await asyncio.gather(*(server.serve() for server in servers))


if __name__ == "__main__":
    asyncio.run(main())
