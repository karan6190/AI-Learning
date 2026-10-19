# Lesson 1 — What is MCP? (start here, assumes zero knowledge)

**Goal:** understand *what* MCP is and *why* it exists — before writing any code.
No setup, no running anything. Just the mental model.

---

## 1. What can an LLM do by itself?

An LLM (Llama, GPT, Claude…) is a **text-in, text-out** machine. You give it text, it
predicts text back. That is *all* it does on its own.

So if you ask it *"what files are in my GitHub repo?"* — it **cannot answer**. It has no
eyes, no hands, no internet. It might *make up* a convincing list, but it can't actually
look. It's a brilliant **brain in a jar with no arms**.

## 2. Tools give the brain arms

To make an LLM useful, we give it **tools**. A tool is just:

> **a function the model is allowed to ask us to run.**

Crucial point: the model **never runs code itself**. It only *asks*. The loop looks like this:

```
You:        "What files are in my repo?"
Model:      "I'd like to call the tool  list_files(repo='my-project')"   ← it just asks
Your code:  actually runs list_files('my-project')  →  ["README.md", "app.py"]
You:        "The tool returned: README.md, app.py"                        ← you feed it back
Model:      "Your repo has two files: README.md and app.py."              ← now it can answer
```

That loop — **model asks → your code runs it → you return the result → model continues** —
is what people call an **agent**.

## 3. The problem MCP solves

Say you want your AI app to use tools from GitHub, Slack, *and* a database.

Before MCP, you hand-wired **every one yourself**. GitHub's API works one way, Slack's
another, the database another — all custom glue code. Worse: if a coworker already wrote
great GitHub tools for *their* app, you couldn't reuse them. Their glue didn't fit your app.

It was the mess of **every device needing its own charger cable**.

## 4. MCP = the universal plug

**MCP (Model Context Protocol)** is an agreed standard for how an AI app and a set of tools
talk to each other.

> MCP is **USB-C for AI tools.**

Once everyone speaks MCP:

- Someone writes the GitHub tools **once**, as an **MCP server**.
- *Any* app that speaks MCP (your app, a coworker's app, Claude Desktop, Cursor…) can plug
  into that server and use those tools — **no custom glue**.

MCP is **not** a library or an AI model. It's a **protocol** — a set of rules for the
conversation. Just like **HTTP** is the rulebook browsers and web servers follow, **MCP** is
the rulebook AI apps and tools follow.

## 5. The two roles: server and client

Every MCP setup has exactly two sides:

| Role | What it does | Analogy |
|------|--------------|---------|
| **MCP server** | *Offers* tools: "here's what I can do: `list_files`, `read_file`…" | A wall socket providing power |
| **MCP client** | *Uses* tools on the LLM's behalf: "what do you offer? OK, run `list_files`." | A device that plugs in |

They are **separate programs**. They don't share code — they just talk over the MCP protocol.
That separation is the whole point: **swap either side without touching the other.**

## 6. The two things a client always does

1. **Discovery** — on connect, the client asks the server *"what tools do you have?"* and gets
   back a list of names + descriptions. Nothing is hard-coded; it's discovered at connect time.
2. **Calling** — when the LLM wants a tool, the client forwards the request to the server, the
   server runs it, and the result comes back.

---

## The one picture to remember

```
   ┌─────────────┐     "what tools do you have?"      ┌─────────────┐
   │ MCP CLIENT  │  ───────────────────────────────►  │ MCP SERVER  │
   │ (your app + │  ◄───  list_files, read_file  ───  │ (offers the │
   │  the LLM)   │                                     │   tools)    │
   │             │  ───  "run list_files('x')"  ────►  │             │
   │             │  ◄──────  ["README.md"]  ─────────  │             │
   └─────────────┘                                     └─────────────┘
         ▲                                                    │
         │ the LLM decides WHICH tool to call                 │ actually DOES the work
         │ and reads the result                               │ (talks to GitHub, a DB, files…)
```

## Check yourself

- Can an LLM read your files on its own? *(No — it needs a tool.)*
- Who actually runs a tool — the model, or your code? *(Your code. The model only asks.)*
- Is MCP a program you install? *(No — it's a protocol, a set of rules. Programs implement it.)*
- What are the two roles? *(Server = offers tools. Client = uses them for the LLM.)*

## Next lesson

Lesson 2 — build the smallest possible **MCP server** yourself (a couple of tools) and watch
a client discover them. That's where we finally write code.
