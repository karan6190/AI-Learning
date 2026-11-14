# A2A Hands-On Lab — Parse an Agent Card, then let a supervisor discover agents

Two exercises that turn the [A2A explainer](../README.md) into running code:

1. **Parse an Agent Card**: read a card the way a client agent does: *who, where, what, how, auth*.
2. **A supervisor that discovers agents**: run three tiny A2A agents (Calculator, Weather, Joke).
   A supervisor reads their Agent Cards to see **who is available**, then sends each user
   request to the agent whose skill fits.

**No API key needed.** Everything runs locally, and the agents are plain Python with no LLM.

| File | What it is |
|---|---|
| [`sample_agent_card.json`](sample_agent_card.json) | A realistic Agent Card (spec 1.0) for an imaginary *Expense Agent* |
| [`01_parse_agent_card.py`](01_parse_agent_card.py) | Exercise 1: parse, validate and query an Agent Card, offline |
| [`02_basic_agents.py`](02_basic_agents.py) | Exercise 2: three basic A2A agents, each with its own Agent Card and port |
| [`03_supervisor.py`](03_supervisor.py) | Exercise 2: the supervisor; it discovers agents by card and delegates to them |

---

## Setup

```bash
# from inside the a2a folder
python -m venv .venv
#   Windows (Git Bash):   source .venv/Scripts/activate
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   macOS / Linux:         source .venv/bin/activate
pip install -r requirements.txt
```

> **Heads-up: spec versions.** `a2a-sdk` 1.x implements **A2A spec 1.0**. Older blog posts and
> samples use **0.3** names (`message/send`, `"kind": "text"`, a top-level `"url"` in the card).
> This lab uses the 1.0 names throughout; the table at the bottom maps old → new.

---

## Exercise 1 · Parse an Agent Card

```bash
python lab/01_parse_agent_card.py
```

### The idea

Before a client agent sends anything, it reads the remote agent's card and answers five questions:

| Question | Card field(s) |
|---|---|
| **WHO** is this? | `name`, `description`, `version`, `provider` |
| **WHERE** do I send requests? | `supportedInterfaces[]`: each has a `url` + `protocolBinding` (`JSONRPC`, `HTTP+JSON`, `GRPC`) |
| **WHAT** can it do? | `skills[]`: `id`, `description`, `tags`, `examples` |
| **HOW** should I talk to it? | `capabilities.streaming`, `capabilities.pushNotifications`, `defaultInputModes` / `defaultOutputModes` |
| **AM I ALLOWED?** | `securitySchemes` (what auth exists) + `securityRequirements` (what's demanded) |

### What the script does

```
 sample_agent_card.json ──► STEP 1 json.loads ──► dict
                         ──► STEP 2 parse_agent_card() ──► typed AgentCard   (same parser the SDK client uses)
                         ──► STEP 3 validate + answer WHO/WHERE/WHAT/HOW/AUTH
                         ──► STEP 4 pick the best skill for a user request
```

- `parse_agent_card()` is exactly what `A2ACardResolver` runs after it fetches
  `/.well-known/agent-card.json`, so parsing a file offline is the same as discovering a live agent.
- `pick_interface()` shows a client choosing **which endpoint** to call when an agent offers several bindings.
- `best_skill()` is toy keyword matching. In a real orchestrator an LLM reads the skill
  descriptions and picks one. That's why **good skill descriptions matter**: they are the
  prompt the calling agent routes on.

### Expected output (abridged)

```
=== What a client learns from this card ===
WHO    : Expense Agent v1.2.0 — Checks trip costs against company travel policy and team budgets.
WHERE  : https://expense-agent.example.com/a2a/jsonrpc  (JSONRPC)
HOW    : streaming=True  push=True  in=['text/plain', 'application/json'] ...
AUTH   : corp_sso: open_id_connect_security_scheme
WHAT   :
   - [check_trip_budget] Check trip budget  tags=['finance', 'travel', 'policy'] ...
   - [explain_policy] Explain travel policy  tags=['policy', 'travel', 'faq']  out=['text/plain']

STEP 4 · routing user requests to a skill:
  'Is my 4 night trip to Singapore within budget?'  -> check_trip_budget
  'Am I allowed to fly business class?'             -> explain_policy
```

### Try it

1. **Break the card.** Delete `"supportedInterfaces"` from the JSON and re-run. `validate()` reports
   that a client has nowhere to send requests.
2. **Add a skill.** Add a `"book_flight"` skill and a request that should route to it.
3. **Read a v0.3 card.** Replace `supportedInterfaces` with an old-style top-level
   `"url": "https://..."`. The parser converts it into a `supportedInterfaces` entry for you
   (tagged `protocolVersion 0.3.0`, so a client knows to speak the old dialect).
4. **Parse a live card from Exercise 2:** once the agents are running,
   `curl http://localhost:9001/.well-known/agent-card.json > live.json` then
   `python lab/01_parse_agent_card.py live.json`.

---

## Exercise 2 · A supervisor that discovers agents by their Agent Cards

### The idea

The supervisor starts with only a **list of URLs**. It doesn't know what any of the agents
do until it reads their Agent Cards. That is A2A discovery: agents describe themselves, and
callers decide based on the description.

```
                         ┌──────────────── 03_supervisor.py ────────────────┐
   "What is 12 plus 30?" │ STEP 1  DISCOVER  read every agent's card         │
   ────────────────────► │ STEP 2  ROUTE     match the request to a skill    │
                         │ STEP 3  DELEGATE  send it to that agent over A2A  │
                         └───────┬──────────────────┬──────────────────┬─────┘
          GET agent-card.json    │                  │                  │
          then SendMessage       ▼                  ▼                  ▼
                       ┌──────────────────┐ ┌────────────────┐ ┌───────────────┐
                       │ Calculator Agent │ │ Weather Agent  │ │  Joke Agent   │
                       │ :9001            │ │ :9002          │ │  :9003        │
                       │ skill add_numbers│ │ skill          │ │ skill         │
                       │                  │ │ get_weather    │ │ tell_joke     │
                       └──────────────────┘ └────────────────┘ └───────────────┘
                                    02_basic_agents.py (3 servers, 1 script)
```

### Run it

```bash
# terminal 1: start the three agents
python lab/02_basic_agents.py

# terminal 2: look at one agent's business card
curl http://localhost:9001/.well-known/agent-card.json

# terminal 2: run the supervisor
python lab/03_supervisor.py
python lab/03_supervisor.py "What is 7 plus 8 plus 9?"     # or ask your own
```

### Expected output

```
STEP 1 · discovering agents from their Agent Cards...
  (no agent answering at http://localhost:9004 — skipping)

Available agents (3):
  AGENT              SKILL         TAGS                                         ENDPOINT
  Calculator Agent   add_numbers   math, add, plus, sum, calculate              http://localhost:9001/a2a/jsonrpc
  Weather Agent      get_weather   weather, temperature, forecast, rain, sunny  http://localhost:9002/a2a/jsonrpc
  Joke Agent         tell_joke     joke, funny, laugh, humor                    http://localhost:9003/a2a/jsonrpc

STEP 2 + 3 · routing and delegating requests:

  User      : What is 12 plus 30?
  Supervisor: -> Calculator Agent
  Calculator Agent: 12 + 30 = 42

  User      : What's the weather in London?
  Supervisor: -> Weather Agent
  Weather Agent: It's 5°C and rainy in London.

  User      : Tell me a joke
  Supervisor: -> Joke Agent
  Joke Agent: I asked an AI agent to tell me a joke about UDP. It didn't care if I got it.

  User      : Book me a flight to Paris
  Supervisor: no available agent has a skill for this.
```

Two outcomes are deliberate:
- **`localhost:9004` is in the supervisor's list, but nothing runs there.** Discovery skips it,
  just as a real system has to cope with an agent that's down.
- **"Book me a flight"** matches no agent's skill, so the supervisor says so instead of guessing.

### How the agents work (`02_basic_agents.py`)

Each agent is three pieces. The code is the same for all three; only the card and the "brain" change.

**1. The Agent Card**: the agent's description of itself. The supervisor routes on the `skills`,
especially their `tags`:

```python
make_card("Calculator Agent", "Does simple arithmetic.", 9001,
          AgentSkill(id="add_numbers", name="Add numbers",
                     description="Adds up all the numbers found in your message.",
                     tags=["math", "add", "plus", "sum", "calculate"],
                     examples=["What is 12 plus 30?"]))
```

**2. The Executor**: receives the A2A message, calls the brain, and sends back a reply:

```python
async def execute(self, context, event_queue):
    question = context.get_user_input()      # text the client sent
    answer = self.brain(question)            # plain Python function
    await event_queue.enqueue_event(new_text_message(answer, context_id=context.context_id))
```

The answer is instant, so the agent replies with a single **Message** and creates no Task.
A long-running agent would create a **Task** and send status updates instead (see section 3.2 of
the [explainer](../README.md#task-the-unit-of-work)).

**3. The server**: the SDK provides the routes for the card and for JSON-RPC:

```python
handler = DefaultRequestHandler(agent_executor=SimpleExecutor(card.name, brain),
                                task_store=InMemoryTaskStore(), agent_card=card)
routes  = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/a2a/jsonrpc")
app     = Starlette(routes=routes)
```

### How the supervisor works (`03_supervisor.py`)

| Step | Function | What it does |
|---|---|---|
| 1 · Discover | `discover_agents()` | `A2ACardResolver(...).get_agent_card()` on every URL; skips agents that don't answer |
| | `print_directory()` | Prints each agent, its skills, tags and endpoint, all read **from the cards** |
| 2 · Route | `choose_agent()` | Scores each skill by how many of its `tags` appear in the request, and picks the highest |
| 3 · Delegate | `ask_agent()` | `create_client(card)` connects to the endpoint listed in the card, then `send_message(...)` |

> **This is the same supervisor idea** as the
> [Multi-agent-parallel-execution course](../../Multi-agent-parallel-execution/), with one
> difference: the workers are now **separate services** found through their Agent Cards, not
> nodes hard-wired into one graph. Add a new agent and the supervisor can use it without any code change.

### See the raw protocol (no SDK)

A2A is just HTTP + JSON-RPC, so you can talk to an agent with `curl`:

```bash
curl -s -X POST http://localhost:9001/a2a/jsonrpc \
  -H "Content-Type: application/json" \
  -H "A2A-Version: 1.0" \
  -d '{
    "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
    "params": { "message": {
        "role": "ROLE_USER", "messageId": "m1",
        "parts": [ { "text": "What is 2 plus 3?" } ] } }
  }'
```

> **Gotcha:** leave out the `A2A-Version: 1.0` header and the server assumes the client
> speaks **0.3**, so it rejects the call with `-32009 VERSION_NOT_SUPPORTED`. The SDK client
> sends the header for you; raw `curl` doesn't.

### Try it

1. **Stop an agent.** Comment out the Joke Agent in `AGENTS`, restart, and run the supervisor.
   It disappears from the directory, and "Tell me a joke" now gets "no available agent".
2. **Add a fourth agent.** Give it port 9004 (already in the supervisor's list), a brain
   function and a skill, e.g. a *Translator Agent* with tags `["translate", "french"]`.
   Restart the agents and run the supervisor; it finds and uses the new agent **without any change to `03_supervisor.py`**.
3. **Spot a routing mistake.** Run `python lab/03_supervisor.py "Is it sunny enough to add a picnic?"`.
   It goes to the **Calculator** agent, not Weather. Why? (Hint: the tag `add` is found inside
   the request, and so is `sunny`, so the two agents tie.) Keyword matching is brittle, which is
   why real supervisors use an LLM (next exercise).
4. **Route with an LLM.** Replace `choose_agent()` with an LLM call that reads each skill's
   `description` and picks one. The cards are the prompt.
5. **Parse a live card** with Exercise 1: `curl http://localhost:9002/.well-known/agent-card.json > live.json`
   then `python lab/01_parse_agent_card.py live.json`.

---

## A2A spec 0.3 → 1.0 cheat sheet

| Concept | 0.3 (older samples) | 1.0 (this lab, `a2a-sdk` 1.x) |
|---|---|---|
| Where to call | top-level `"url"` + `"preferredTransport"` | `"supportedInterfaces": [{url, protocolBinding, protocolVersion}]` |
| Send / stream | `message/send`, `message/stream` | `SendMessage`, `SendStreamingMessage` |
| Get / cancel | `tasks/get`, `tasks/cancel` | `GetTask`, `CancelTask` (also `ListTasks`) |
| Re-attach to stream | `tasks/resubscribe` | `SubscribeToTask` |
| Roles | `"user"`, `"agent"` | `"ROLE_USER"`, `"ROLE_AGENT"` |
| Parts | `{"kind": "text", "text": …}` | `{"text": …}`, `{"data": …}`, `{"url": …}`, `{"raw": …}` |
| Task states | `working`, `completed`, `input-required` | `TASK_STATE_WORKING`, `TASK_STATE_COMPLETED`, `TASK_STATE_INPUT_REQUIRED` |
| Version negotiation | none | `A2A-Version` HTTP header |
