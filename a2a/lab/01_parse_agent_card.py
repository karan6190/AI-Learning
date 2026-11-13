"""
LAB 1 — Parse and read an A2A Agent Card (offline, no server, no API key)
=========================================================================

An Agent Card is the JSON "business card" an agent publishes at
    https://<host>/.well-known/agent-card.json

Before a client agent talks to a remote agent, it reads this card to answer:
    1. WHO is this?            -> name, description, provider, version
    2. WHERE do I call it?     -> supportedInterfaces (url + protocol binding)
    3. WHAT can it do?         -> skills
    4. HOW should I talk?      -> capabilities (streaming? push?) + input/output modes
    5. AM I ALLOWED?           -> securitySchemes + securityRequirements

This script does exactly that for `sample_agent_card.json`, in four steps:
    STEP 1  read the raw JSON  (it's just a dict)
    STEP 2  parse it into the SDK's typed AgentCard  (same parser the client uses)
    STEP 3  pull out the answers to the 5 questions above
    STEP 4  pick the best skill for a user request  (a toy version of "routing")

Run it:   python lab/01_parse_agent_card.py
          python lab/01_parse_agent_card.py path/to/another-card.json
"""

import json
import sys
from pathlib import Path

from a2a.client.card_resolver import parse_agent_card
from a2a.helpers import display_agent_card
from a2a.types import AgentCard

CARD_PATH = Path(__file__).parent / "sample_agent_card.json"


# ---------------------------------------------------------------------------
# STEP 1 — the card is just JSON
# ---------------------------------------------------------------------------
def load_raw(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# STEP 2 — parse into a typed AgentCard
#   parse_agent_card() is what A2ACardResolver calls after fetching the URL.
#   It also upgrades older (v0.3) cards, e.g. a top-level "url" field becomes
#   a supportedInterfaces entry.
# ---------------------------------------------------------------------------
def parse(raw: dict) -> AgentCard:
    return parse_agent_card(raw)


# ---------------------------------------------------------------------------
# STEP 3 — answer the five questions a client cares about
# ---------------------------------------------------------------------------
def validate(card: AgentCard) -> list[str]:
    """Return a list of problems. Empty list = the card is usable."""
    problems = []
    if not card.name:
        problems.append("missing 'name'")
    if not card.supported_interfaces:
        problems.append("missing 'supportedInterfaces' — a client has nowhere to send requests")
    if not card.skills:
        problems.append("no 'skills' — a client can't tell what this agent does")
    for skill in card.skills:
        if not skill.id or not skill.description:
            problems.append(f"skill {skill.name!r} needs an 'id' and a 'description'")
    return problems


def pick_interface(card: AgentCard, preferred: str = "JSONRPC") -> tuple[str, str]:
    """WHERE: choose the endpoint to call. Prefer our binding, else the agent's first one."""
    for iface in card.supported_interfaces:
        if iface.protocol_binding == preferred:
            return iface.url, iface.protocol_binding
    first = card.supported_interfaces[0]
    return first.url, first.protocol_binding


def describe_security(card: AgentCard) -> list[str]:
    """AM I ALLOWED: which auth schemes does the agent accept?"""
    lines = []
    for name, scheme in card.security_schemes.items():
        kind = scheme.WhichOneof("scheme")          # e.g. "open_id_connect_security_scheme"
        lines.append(f"{name}: {kind}")
    return lines or ["(none declared — open agent, fine for local demos only)"]


def print_summary(card: AgentCard) -> None:
    url, binding = pick_interface(card)
    print("\n=== What a client learns from this card ===")
    print(f"WHO    : {card.name} v{card.version} — {card.description}")
    print(f"WHERE  : {url}  ({binding})")
    print(f"HOW    : streaming={card.capabilities.streaming}  "
          f"push={card.capabilities.push_notifications}  "
          f"in={list(card.default_input_modes)}  out={list(card.default_output_modes)}")
    print("AUTH   : " + "; ".join(describe_security(card)))
    print("WHAT   :")
    for skill in card.skills:
        # A skill may override the agent-wide output modes.
        out = list(skill.output_modes) or list(card.default_output_modes)
        print(f"   - [{skill.id}] {skill.name}  tags={list(skill.tags)}  out={out}")
        for ex in skill.examples:
            print(f"       e.g. {ex!r}")


# ---------------------------------------------------------------------------
# STEP 4 — choose a skill for a request (toy keyword matching)
#   A real orchestrator would let an LLM read the skill descriptions instead.
# ---------------------------------------------------------------------------
def best_skill(card: AgentCard, request: str):
    words = set(request.lower().replace("?", "").split())

    def score(skill) -> int:
        text = " ".join([skill.name, skill.description, *skill.tags, *skill.examples]).lower()
        return sum(1 for w in words if len(w) > 3 and w in text)

    ranked = sorted(card.skills, key=score, reverse=True)
    return ranked[0], score(ranked[0])


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else CARD_PATH

    raw = load_raw(path)
    print(f"STEP 1 · raw JSON has keys: {sorted(raw)}")

    card = parse(raw)
    print(f"STEP 2 · parsed into {type(card).__name__} with {len(card.skills)} skill(s)")

    problems = validate(card)
    if problems:
        print("\nCard has problems:")
        for p in problems:
            print("  ✗", p)
        sys.exit(1)

    print("\nSTEP 3 · the SDK's own pretty-printer:")
    display_agent_card(card)
    print_summary(card)

    print("\nSTEP 4 · routing user requests to a skill:")
    for request in [
        "Is my 4 night trip to Singapore within budget?",
        "Am I allowed to fly business class?",
    ]:
        skill, s = best_skill(card, request)
        print(f"  {request!r}\n     -> {skill.id}  (score {s})")
