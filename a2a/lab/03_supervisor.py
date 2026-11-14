"""
LAB 3 — A supervisor that finds agents by their Agent Cards and delegates to them
================================================================================

The supervisor knows only a list of agent URLs. It knows nothing about what
those agents do. It learns that from their Agent Cards:

    STEP 1  DISCOVER   fetch every agent's /.well-known/agent-card.json
                       and print a table of who is available and their skills
    STEP 2  ROUTE      for each request, pick the agent whose skill best matches
                       (simple keyword matching on the skill tags)
    STEP 3  DELEGATE   send the request to that agent over A2A and print its reply

        Supervisor ──GET agent-card.json──► Calculator / Weather / Joke agents
                   ──SendMessage──────────► the agent it chose
                   ◄──reply Message──────── that agent

Start the agents first:   python lab/02_basic_agents.py
Then run:                 python lab/03_supervisor.py
Or ask your own question: python lab/03_supervisor.py "What is 7 plus 8 plus 9?"
"""

import asyncio
import sys

import httpx

from a2a.client import A2ACardResolver, AgentCardResolutionError, ClientConfig, create_client
from a2a.helpers import get_message_text, new_text_message
from a2a.types import AgentCard, Role, SendMessageRequest

# The supervisor's "phone book". Add a URL here and the supervisor can use that agent.
AGENT_URLS = [
    "http://localhost:9001",
    "http://localhost:9002",
    "http://localhost:9003",
    "http://localhost:9004",   # nothing runs here: shows what happens when an agent is down
]

DEMO_REQUESTS = [
    "What is 12 plus 30?",
    "What's the weather in London?",
    "Tell me a joke",
    "Book me a flight to Paris",   # no agent has this skill
]


# ---------------------------------------------------------------------------
# STEP 1 — discover: read each agent's card
# ---------------------------------------------------------------------------
async def discover_agents(urls: list[str]) -> list[AgentCard]:
    cards = []
    async with httpx.AsyncClient() as http:
        for url in urls:
            try:
                cards.append(await A2ACardResolver(http, url).get_agent_card())
            except AgentCardResolutionError:
                print(f"  (no agent answering at {url} — skipping)")
    return cards


def print_directory(cards: list[AgentCard]) -> None:
    print(f"\nAvailable agents ({len(cards)}):")
    print(f"  {'AGENT':<18} {'SKILL':<13} {'TAGS':<44} ENDPOINT")
    for card in cards:
        for skill in card.skills:
            tags = ", ".join(skill.tags)
            print(f"  {card.name:<18} {skill.id:<13} {tags:<44} {card.supported_interfaces[0].url}")


# ---------------------------------------------------------------------------
# STEP 2 — route: which agent's skill matches the request best?
#   Count how many of the skill's tags appear in the request.
#   A real supervisor would let an LLM read the skill descriptions instead.
# ---------------------------------------------------------------------------
def choose_agent(cards: list[AgentCard], request: str) -> AgentCard | None:
    words = request.lower()
    best_card, best_score = None, 0
    for card in cards:
        for skill in card.skills:
            score = sum(1 for tag in skill.tags if tag in words)
            if score > best_score:
                best_card, best_score = card, score
    return best_card


# ---------------------------------------------------------------------------
# STEP 3 — delegate: send the request over A2A, get the reply
# ---------------------------------------------------------------------------
async def ask_agent(card: AgentCard, request: str) -> str:
    client = await create_client(card, client_config=ClientConfig(streaming=False))
    message = new_text_message(request, role=Role.ROLE_USER)
    async with client:
        async for response in client.send_message(SendMessageRequest(message=message)):
            return get_message_text(response.message)
    return "(no reply)"


async def main(requests: list[str]) -> None:
    print("STEP 1 · discovering agents from their Agent Cards...")
    cards = await discover_agents(AGENT_URLS)
    print_directory(cards)

    print("\nSTEP 2 + 3 · routing and delegating requests:")
    for request in requests:
        print(f"\n  User      : {request}")
        card = choose_agent(cards, request)
        if card is None:
            print("  Supervisor: no available agent has a skill for this.")
            continue
        print(f"  Supervisor: -> {card.name}")
        print(f"  {card.name}: {await ask_agent(card, request)}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or DEMO_REQUESTS))
