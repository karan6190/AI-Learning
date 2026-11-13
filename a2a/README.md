# A2A — Letting AI Agents Talk to Each Other Through a Standard Protocol

An explainer, from zero, on the **Agent2Agent (A2A) protocol**: the open standard that lets
**one AI agent find, talk to, and hand work to another AI agent**, even when the two were built
by different teams, on different frameworks, by different vendors.

If [MCP](../mcp/) is **USB-C for AI tools**, A2A is **email/phone for AI agents**: a common way
for independent agents to reach each other and work together.

---

## Contents

1. [What is A2A?](#1-what-is-a2a)
2. [A2A vs MCP: what's the difference?](#2-a2a-vs-mcp--whats-the-difference)
3. [A2A architecture](#3-a2a-architecture)
4. [Putting it together: one request, end to end](#4-putting-it-together--one-request-end-to-end)
5. [Glossary](#5-glossary)
6. [Further reading](#6-further-reading)

---

## 1. What is A2A?

### The problem

Companies are now building **lots of agents**: a travel agent, an HR agent, an expense agent, a
data-analysis agent. Each one is built by a different team, often on a different stack
(LangGraph, CrewAI, Google ADK, Semantic Kernel, a vendor SaaS product…).

Sooner or later one agent needs help from another:

> *"Book my trip to Houston"* → the **travel agent** needs the **expense agent** to check the
> budget and the **calendar agent** to find free dates.

Without a standard, every pair of agents needs **custom glue**: a bespoke API, a bespoke
auth scheme, a bespoke way of saying "this is still running, check back later." With N agents
you end up with roughly N² integrations.

### The answer

**A2A is an open protocol for agent-to-agent communication.** It was introduced by Google in
April 2025 and is now an open-source project under the **Linux Foundation**, backed by a large
group of tech and enterprise companies.

It standardises four things:

| A2A standardises… | So that… |
|---|---|
| **Discovery**: how an agent describes itself (the **Agent Card**) | a client can find out *what an agent can do* and *how to call it* |
| **Messaging**: the shape of a request and reply (**Messages** made of **Parts**) | text, files and structured JSON all travel the same way |
| **Task lifecycle**: how long-running work is tracked (**Tasks** with states) | work that takes seconds, hours, or needs human input is handled the same way |
| **Transport & security**: HTTP, JSON-RPC, streaming, standard auth | it plugs into existing web infrastructure, gateways and identity providers |

### Key design principles

- **Agents stay opaque.** An agent does *not* expose its prompts, memory, internal tools or
  model. It only exposes *skills* ("I can book flights"). This protects IP and security, and
  means you can swap the internals without breaking callers.
- **Built on existing web standards.** HTTP(S), JSON-RPC 2.0, Server-Sent Events (SSE), and
  OpenAPI-style auth schemes. Nothing exotic, so it works with your existing proxies, gateways,
  logging and identity providers.
- **Async-first.** Real agent work can be slow or need a human in the loop. A2A treats
  long-running tasks as normal, not an edge case.
- **Modality-agnostic.** Messages can carry text, files, structured data, and the protocol
  allows for richer content such as forms, audio or video.
- **Secure by default.** Agents declare their auth requirements up front; enterprise auth
  (OAuth 2.0, OpenID Connect, API keys, mTLS) is used instead of anything custom.

### The one idea

```
   ┌──────────────┐   "who are you, what can you do?"   ┌──────────────┐
   │  CLIENT      │  ─────────────────────────────────► │  REMOTE      │
   │  AGENT       │  ◄────────  Agent Card  ──────────  │  AGENT       │
   │  (needs help)│  ───  "please do this task"  ─────► │  (does the   │
   │              │  ◄───  status… status… result  ───  │   work)      │
   └──────────────┘                                     └──────────────┘
     decides WHO to ask                                   decides HOW to do it
```

---

## 2. A2A vs MCP: what's the difference?

This is the most common point of confusion. **They are not competitors; they solve different
problems and are designed to be used together.**

### The short version

> **MCP connects an agent to its *tools*. A2A connects an agent to *other agents*.**
>
> MCP is **vertical** (agent ↓ down to tools and data). A2A is **horizontal** (agent ↔ agent).

### An analogy: the car repair shop

(This is the analogy used in the A2A docs.)

- A **mechanic** (an agent) uses **tools**: a wrench, a diagnostic scanner, a parts database.
  The tools do exactly what they're told and nothing more. **That's MCP**: structured,
  predictable calls like `raise_platform(height=2m)`.
- A **customer** talks to the **shop manager**, who talks to the **mechanic**, who calls a
  **parts supplier**. These are all *autonomous parties* having a conversation: *"My car makes
  a rattling noise."* / *"Can you send a photo?"* / *"That part is back-ordered, is a substitute
  OK?"* **That's A2A**: open-ended, multi-turn, sometimes slow, between peers that each think
  for themselves.

### Side-by-side comparison

| | **MCP** (Model Context Protocol) | **A2A** (Agent2Agent Protocol) |
|---|---|---|
| **Created by** | Anthropic (Nov 2024) | Google (Apr 2025), now Linux Foundation |
| **Connects** | Agent / LLM app → **tools, data, resources** | Agent → **another agent** |
| **Direction** | Vertical (agent uses a capability) | Horizontal (peer collaboration) |
| **The other side is…** | A **tool**: deterministic, does what it's told, no reasoning | An **agent**: autonomous, reasons, may ask questions back, may refuse |
| **Interaction style** | Function call: `call_tool(name, args)` → result | Conversation / delegation: send a message, get a **task** that evolves over time |
| **Typical duration** | Short, usually synchronous | Seconds to hours or days; async is normal |
| **Multi-turn?** | Not really; one call, one result | Yes; the remote agent can reply `input-required` and wait for more info |
| **What's exposed** | Precise **tool schemas** (name, typed input parameters) | High-level **skills** described in an **Agent Card**; internals stay hidden |
| **Discovery** | Client asks the server `tools/list` after connecting | Client fetches the **Agent Card** (usually at `/.well-known/agent-card.json`) *before* connecting |
| **Core objects** | Tools, Resources, Prompts | Agent Card, Task, Message, Part, Artifact |
| **Transport** | stdio (local) or Streamable HTTP | HTTP(S) with JSON-RPC 2.0, plus SSE streaming, webhooks, and gRPC / REST bindings |
| **Typical deployment** | Often local / same machine (e.g. a desktop app launching a server) | Networked services, often across teams or organisations |
| **Question it answers** | *"How does my agent **use** this capability?"* | *"How does my agent **work with** that other agent?"* |

### How they fit together

A real system typically uses **both**:

```
                        User
                         │
                         ▼
               ┌───────────────────┐
               │   Travel Agent    │  (A2A client)
               └───────────────────┘
                 │A2A            │A2A
                 ▼               ▼
       ┌───────────────┐  ┌────────────────┐
       │ Expense Agent │  │ Calendar Agent │   (A2A servers / remote agents)
       └───────────────┘  └────────────────┘
          │MCP    │MCP          │MCP
          ▼       ▼             ▼
       ┌─────┐ ┌──────┐     ┌──────────┐
       │ SAP │ │Policy│     │ Outlook  │     (MCP servers = tools & data)
       │ API │ │ DB   │     │ Graph API│
       └─────┘ └──────┘     └──────────┘

   A2A = horizontal, agent ↔ agent         MCP = vertical, agent → tools
```

- The **Travel Agent** doesn't know or care that the Expense Agent uses SAP; it just asks,
  over A2A, *"is this trip within budget?"*
- The **Expense Agent** uses MCP internally to query SAP and the policy database.
- Each team owns their agent end-to-end and can change its tools without breaking anyone.

### Rule of thumb: which one do I need?

| If you want to… | Use |
|---|---|
| Give your agent access to a database, API, file system, or SaaS app | **MCP** |
| Let your agent delegate a goal to another agent that owns a domain | **A2A** |
| Expose your agent so *other teams'* agents can use it | **A2A** (publish an Agent Card) |
| Expose a simple, deterministic function | **MCP** (making it an agent is overkill) |
| Work that is long-running, multi-turn, or needs human approval mid-way | **A2A** |

> **Grey area:** you *can* wrap an agent as an MCP tool, and some people do. It works for
> simple cases, but you lose A2A's task lifecycle, multi-turn `input-required` flow,
> streaming status updates and push notifications. If the thing on the other side *thinks*,
> A2A is the better fit.

---

## 3. A2A architecture

### 3.1 The actors

```
   ┌────────┐        ┌──────────────────┐   A2A protocol   ┌──────────────────┐
   │  User  │ ─────► │  A2A Client      │ ───────────────► │  A2A Server      │
   │(human  │        │  (client agent)  │ ◄─────────────── │  (remote agent)  │
   │or app) │        │                  │                  │                  │
   └────────┘        └──────────────────┘                  └──────────────────┘
                     acts on the user's                     exposes an HTTP endpoint,
                     behalf, picks which                    does the work, reports
                     remote agent to call                   progress and results
```

| Actor | Role |
|---|---|
| **User** | The human (or automated system) with a goal. |
| **A2A Client** (client agent) | An app or agent that *initiates* requests on the user's behalf. Discovers remote agents and sends them tasks. |
| **A2A Server** (remote agent) | An agent that exposes an A2A-compliant HTTP endpoint. Receives requests, does the work, returns results. **Opaque**: the client sees only its Agent Card and its outputs. |

An agent can be **both**: a client to agents downstream and a server to agents upstream. That's
how you build chains and meshes of agents.

### 3.2 The core building blocks

```
  Agent Card ── "here's who I am and what I can do"     (discovery)
       │
       ▼
  Message ───── one turn of conversation                (communication)
    └─ Part ─── a piece of content: text | file | data
       │
       ▼
  Task ──────── a unit of work with an id and a state   (lifecycle)
    ├─ status   submitted → working → completed …
    ├─ history  the Messages exchanged so far
    └─ Artifact the outputs produced (made of Parts)
```

#### Agent Card: discovery

A JSON document that acts as the agent's **business card**. It's normally published at a
well-known URL:

```
https://expense-agent.example.com/.well-known/agent-card.json
```

It tells a client **what** the agent can do, **where** to call it, and **how** to authenticate:

```json
{
  "name": "Expense Agent",
  "description": "Checks trip costs against company travel policy and budgets.",
  "url": "https://expense-agent.example.com/a2a",
  "version": "1.2.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "securitySchemes": {
    "oauth": { "type": "openIdConnect", "openIdConnectUrl": "https://login.example.com/.well-known/openid-configuration" }
  },
  "security": [{ "oauth": [] }],
  "defaultInputModes": ["text/plain", "application/json"],
  "defaultOutputModes": ["text/plain", "application/json"],
  "skills": [
    {
      "id": "check_trip_budget",
      "name": "Check trip budget",
      "description": "Given a trip itinerary and cost, says whether it is within policy and budget.",
      "tags": ["finance", "travel", "policy"],
      "examples": ["Is a $1,800 trip to Houston for 3 nights within policy?"]
    }
  ]
}
```

Notice what's **not** there: no prompts, no model name, no list of internal tools. Just skills.

Discovery options:
- **Well-known URL**: fetch `/.well-known/agent-card.json` from the agent's domain.
- **Registry / catalogue**: an enterprise directory of approved agents (common in companies).
- **Direct configuration**: the client is simply told the URL.
- **Extended card**: an agent can return a richer card to *authenticated* clients only.

#### Message and Parts: communication

A **Message** is one turn in the conversation. It has a `role` (`"user"` for the client side,
`"agent"` for the remote agent) and a list of **Parts**:

| Part type | Carries | Example |
|---|---|---|
| **TextPart** | Plain text | `"Is this trip within budget?"` |
| **FilePart** | A file, inline (base64) or by URI | a PDF receipt, an image |
| **DataPart** | Structured JSON | `{"destination": "Houston", "cost": 1800}` |

#### Task: the unit of work

When a client sends a message, the server may answer directly with a Message (quick replies),
or create a **Task**: a stateful object with a unique `id` that tracks the work until it's done.
Related tasks can share a `contextId`, which groups them into one conversation/session.

**Task lifecycle:**

```
                 ┌────────────┐
                 │ submitted  │
                 └─────┬──────┘
                       ▼
                 ┌────────────┐  needs more info   ┌────────────────┐
           ┌───► │  working   │ ─────────────────► │ input-required │
           │     └─────┬──────┘                    └───────┬────────┘
           │           │                                   │
           └───────────┼────── client sends more info ─────┘
                       │
       ┌───────────┬───┴───────┬────────────┐
       ▼           ▼           ▼            ▼
  ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
  │completed│ │ failed │ │ canceled │ │ rejected │      ← terminal states
  └─────────┘ └────────┘ └──────────┘ └──────────┘
```

There is also an `auth-required` state, used when the remote agent needs extra credentials
before it can carry on.

`input-required` is what makes A2A feel like working with a colleague instead of calling a
function: the remote agent can pause and ask *"Economy or business class?"* and the task
resumes when the client answers.

#### Artifact: the output

An **Artifact** is a tangible result of a task: a report, a generated image, a JSON
booking confirmation. Like messages, artifacts are made of Parts, and they can be streamed
in chunks as they're produced.

> **Message vs Artifact:** Messages are the *conversation* ("I'm checking the policy now…").
> Artifacts are the *deliverables* (the final budget-check result).

### 3.3 Three ways to get results back

Because tasks can be quick or very slow, A2A supports three interaction patterns:

```
 1. REQUEST / RESPONSE (+ polling)      good for: quick tasks
    Client ── message/send ──► Server
    Client ◄── Task (working) ─ Server
    Client ── tasks/get ─────► Server   (repeat until done)
    Client ◄── Task (completed) Server

 2. STREAMING (Server-Sent Events)      good for: live progress, incremental output
    Client ── message/stream ─► Server
    Client ◄═ status: working ═ Server
    Client ◄═ artifact chunk  ═ Server
    Client ◄═ status: completed Server   (stream closes)

 3. PUSH NOTIFICATIONS (webhooks)       good for: very long tasks, disconnected clients
    Client ── message/send + webhook URL ─► Server
    ...client disconnects; minutes or hours pass...
    Client's webhook ◄── POST "task completed" ── Server
    Client ── tasks/get ─► Server        (fetch the result)
```

A client only uses streaming or push if the Agent Card says the agent supports it
(`capabilities.streaming`, `capabilities.pushNotifications`).

### 3.4 Security model

A2A deliberately **reuses enterprise security standards** instead of inventing its own:

- **Transport:** HTTPS (TLS) is required in production.
- **Authentication:** declared in the Agent Card using OpenAPI-style `securitySchemes`
  (OAuth 2.0, OpenID Connect, API keys, HTTP bearer, mTLS). Credentials travel in HTTP
  headers, *not* inside A2A messages.
- **Authorization:** the remote agent decides what each caller is allowed to do, often
  per-skill.
- **Opacity:** because internals are never exposed, a compromised client can't read another
  agent's prompts, memory or tool credentials.
- **Webhook safety:** push-notification URLs should be validated and the notifications
  authenticated, to prevent the server being used to hit arbitrary URLs (SSRF).

### 3.5 Inside a remote agent (typical implementation)

The protocol says nothing about *how* the agent works internally, but most SDK-based
implementations (e.g. the official Python `a2a-sdk`) look like this:

```
 ┌──────────────────────── A2A Server (remote agent) ─────────────────────────┐
 │                                                                            │
 │  HTTP layer  ──►  Request Handler  ──►  Agent Executor  ──►  Your agent    │
 │  (serves the      (JSON-RPC methods,     (bridges A2A to      (LangGraph,  │
 │   Agent Card,      validation, auth)      your framework;      CrewAI, ADK,│
 │   /a2a endpoint)        │                 emits status &       plain code) │
 │                         ▼                 artifact events)          │      │
 │                    Task Store                                       ▼      │
 │                    (task state &                               MCP tools,  │
 │                     history)                                   APIs, DBs   │
 └────────────────────────────────────────────────────────────────────────────┘
```

The **Agent Executor** is the piece *you* write: it receives the incoming message, runs your
agent, and publishes events (`working`, artifact chunks, `completed`) that the SDK turns into
A2A responses or SSE streams.

### 3.6 Common topologies

```
  Point-to-point          Orchestrator / supervisor            Mesh / chain
  ──────────────          ─────────────────────────            ────────────
  A ──► B                       Orchestrator                   A ──► B ──► C
                               /     |      \                        │
                              ▼      ▼       ▼                       ▼
                           Agent1  Agent2  Agent3                    D
```

The **orchestrator** pattern is the most common in enterprises: one "front door" agent talks to
the user and delegates over A2A to specialist agents owned by different teams. It's the same
supervisor idea from the [Multi-Agent Systems course](../Multi-agent-parallel-execution/),
except the sub-agents are now **independent services** reachable over the network rather than
nodes in the same graph.

---

## 4. Putting it together: one request, end to end

> User: *"Book me a 3-night trip to Houston next month."*

```
 User        Travel Agent (client)         Expense Agent (remote)      Calendar Agent (remote)
  │                 │                              │                            │
  │── request ─────►│                              │                            │
  │                 │── GET agent-card.json ──────►│                            │
  │                 │◄── card: skill check_budget ─│                            │
  │                 │── GET agent-card.json ───────────────────────────────────►│
  │                 │◄── card: skill find_free_dates ───────────────────────────│
  │                 │                              │                            │
  │                 │── message/stream "free dates next month?" ───────────────►│
  │                 │◄═ working … ═════════════════════════════════════════════ │
  │                 │◄═ artifact: Dec 8–11 ═ completed ═════════════════════════│
  │                 │                              │                            │
  │                 │── message/send "Houston, Dec 8–11, $1,800 ok?" ─►│        │
  │                 │◄── task: input-required "Which cost centre?" ────│        │
  │◄─ "Which cost   │                              │                            │
  │    centre?" ────│                              │                            │
  │── "CC-4410" ───►│                              │                            │
  │                 │── message/send (same taskId) "CC-4410" ─────────►│        │
  │                 │◄── task: completed, artifact {approved: true} ───│        │
  │                 │                              │   (internally used MCP     │
  │◄── "Booked ✓" ──│                              │    to query SAP & policy)  │
```

What each protocol did:
- **A2A**: discovery (Agent Cards), delegation (tasks), streaming progress, a multi-turn
  clarification (`input-required`), and the final artifacts.
- **MCP**: inside the Expense and Calendar agents, to reach SAP, the policy DB and Outlook.

---

## 5. Glossary

| Term | Meaning |
|---|---|
| **A2A** | Agent2Agent protocol: an open standard for agent-to-agent communication |
| **A2A Client** | The agent/app that sends requests to a remote agent |
| **A2A Server / Remote Agent** | The agent that exposes an A2A endpoint and does the work |
| **Agent Card** | JSON "business card" describing an agent's skills, endpoint, capabilities and auth |
| **Skill** | A high-level capability an agent advertises in its card (e.g. "check trip budget") |
| **Task** | A stateful unit of work with an `id` and a lifecycle state |
| **Context (`contextId`)** | Groups related tasks and messages into one conversation |
| **Message** | One conversational turn (`role: user` or `agent`) made of Parts |
| **Part** | A piece of content: `TextPart`, `FilePart`, or `DataPart` |
| **Artifact** | An output/deliverable produced by a task |
| **`input-required`** | Task state meaning "I need more info from you before I continue" |
| **SSE** | Server-Sent Events: how A2A streams live updates over HTTP |
| **Push notification** | A webhook call from the server to the client when a task changes |
| **Opaque agent** | An agent that exposes only skills and results, never its internals |

---

## 6. Further reading

- A2A protocol site & spec: <https://a2a-protocol.org>
- A2A GitHub organisation (spec, SDKs, samples): <https://github.com/a2aproject>
- Python SDK: `pip install a2a-sdk`
- Google's announcement (April 2025): <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/>
- This repo's [MCP course](../mcp/): the "agent → tools" half of the picture
