# LangSmith — LLM-as-Judge Evals & Prompt Hub / Versioning

A teaching kit for two connected topics:

- **Part A — LLM-as-judge evaluations:** score your app's outputs automatically
  by using a second LLM as the grader, over a fixed dataset.
- **Part B — Prompt Hub & versioning:** store prompts in a version-controlled hub
  ("Git for prompts") and pull them into your app at runtime.

They connect: **versioning lets you change a prompt; evals let you prove the change
is better.** That's the real-world workflow.

Runs on **Groq** (the open **gpt-oss** model) — no OpenAI key needed.

---

## What's in this folder

| File | Topic | What it does |
|------|-------|--------------|
| `01_create_dataset.py` | Evals | Creates the `qa-eval-demo` dataset |
| `02_llm_as_judge.py` | Evals | Runs an LLM-as-judge experiment |
| `03_compare_two_prompts.py` | Evals | Compares two prompts with the same judge |
| `04_push_prompt.py` | Prompt Hub | Pushes a prompt (creates v1) |
| `05_pull_and_use_prompt.py` | Prompt Hub | Pulls the prompt and uses it in an app |

---

## Prerequisites

1. LangSmith account + API key → https://smith.langchain.com
2. Groq API key → https://console.groq.com/keys
3. Python 3.9+

Keys come from **Codespace secrets** (`LANGSMITH_API_KEY`, `GROQ_API_KEY`).
Non-secret config is in `.env` (`LANGSMITH_TRACING`, `LANGSMITH_PROJECT`).

---

## Setup

```bash
cd langsmith-evals-prompthub
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Verify:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; \
print('LS key =', bool(os.environ.get('LANGSMITH_API_KEY'))); \
print('Groq   =', bool(os.environ.get('GROQ_API_KEY')))"
```

---

## Run order

**Part A — Evals**
```bash
python 01_create_dataset.py        # once
python 02_llm_as_judge.py          # first experiment
python 03_compare_two_prompts.py   # two experiments to compare
```
Then: LangSmith → **Datasets & Testing** → `qa-eval-demo` → **Experiments**.

**Part B — Prompt Hub**
```bash
python 04_push_prompt.py           # creates v1
python 05_pull_and_use_prompt.py   # pulls + uses it
```
Then: LangSmith → **Prompts** → `qa-answer-prompt` → **history / commits**.

See `TALKING_POINTS.md` for exactly what to show on each screen.

---

## What each program does (in detail)

### `01_create_dataset.py` — build the test set
Creates a **dataset** called `qa-eval-demo` in LangSmith. A dataset is a fixed set
of **examples**; each example has an **input** (a question) and a reference
**output** (the correct "gold" answer).

- No LLM is called here — it's pure data setup.
- It first checks `client.has_dataset(...)` so re-running is safe (it won't create
  duplicates).
- `client.create_dataset(...)` makes the container; `client.create_examples(...)`
  adds the 5 rows.
- **See it:** LangSmith → **Datasets & Testing** → `qa-eval-demo` → **Examples** tab.
- **Why it matters:** a fixed dataset is like unit tests — every experiment runs on
  the *same* questions, so results are comparable over time.

### `02_llm_as_judge.py` — run one LLM-as-judge experiment
Makes the app answer every question, then uses a **second LLM as a grader** to
score each answer against the reference. Produces one **experiment**.

- `target(inputs)` — the app under test: sends the question to `ChatGroq` and
  returns `{"answer": ...}`.
- `correctness(inputs, outputs, reference_outputs)` — the **evaluator** (the
  judge). It uses `with_structured_output(Grade)` so the judge must reply with a
  clean `correct: true/false` + `reason`, not free text. Returns a score of `1`
  (correct) or `0`.
- `evaluate(target, data=..., evaluators=[...], experiment_prefix=...)` — the
  engine: runs the target over every example, scores each with the judge, and
  uploads the results as an experiment.
- **See it:** the dataset → **Experiments** tab → open the `qa-baseline-...` run →
  click a row to see **question → app answer → score + judge's reason**.
- **Why LLM-as-judge:** exact string match is brittle ("Paris" vs "The capital is
  Paris." would fail). A judge grades *meaning*, and its written reason is great for
  debugging.

### `03_compare_two_prompts.py` — prove which prompt is better
Runs the **same dataset + same judge** against **two different system prompts**,
producing two experiments you can compare side by side.

- `make_target(system_prompt)` — a small factory that builds a target using a given
  system prompt, so both runs share identical code and differ only in the prompt.
- `PROMPT_V1` (vague: "Answer the question.") vs `PROMPT_V2` (strict: "answer with
  ONLY the exact fact").
- Calls `evaluate(...)` twice with different `experiment_prefix` values
  (`prompt-v1`, `prompt-v2`).
- **See it:** dataset → **Experiments** → tick both runs → **Compare** → per-example
  scores side by side.
- **Why it matters:** this turns "I think v2 is better" into evidence. This is the
  headline demo of the evals half.

### `04_push_prompt.py` — put a prompt in the Prompt Hub
Pushes a `ChatPromptTemplate` (with a `{question}` variable) to the hub under the
name `qa-answer-prompt`. Each push creates a new immutable **commit** (version).

- `client.push_prompt(PROMPT_NAME, object=prompt)` uploads it and returns a URL.
- **See it:** LangSmith → **Prompts** → `qa-answer-prompt`; note the commit hash.
- **Why it matters:** prompts usually hide, hard-coded, in random files. The hub is
  one versioned home a PM or domain expert can also edit in the UI.

### `05_pull_and_use_prompt.py` — use a hub prompt in an app
Pulls the prompt from the hub at runtime and runs it, instead of hard-coding the
text in the script.

- `client.pull_prompt(PROMPT_NAME)` fetches the latest version; the comment shows
  how to pin an exact version with `name:<commit-hash>` (what production should do).
- `chain = prompt | llm` then `chain.invoke({"question": ...})` — the pulled prompt
  feeds straight into the model.
- **Why it matters:** prompt and code are **decoupled** — improve the prompt in the
  UI and the app picks it up with no redeploy.

---

## Key concepts (the words to teach)

- **Dataset** — a fixed set of example inputs (+ optional reference answers) you
  test against, so results are comparable run to run.
- **Target** — the app/prompt being tested.
- **Evaluator** — a function that scores each output. Here it's an **LLM-as-judge**.
- **Experiment** — one full run of the target over the dataset, with scores.
- **LLM-as-judge** — using a second LLM to grade outputs (handles wording/format
  that exact-match can't).
- **Prompt Hub** — version-controlled storage for prompts, with a UI.
- **Commit / version** — each push is a new immutable version; you can pin, diff,
  and roll back.

---

## Troubleshooting

- **Nothing in LangSmith?** `LANGSMITH_TRACING` must be the string `true`; check the
  keys are set; EU accounts need `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`.
- **`push_prompt`/`pull_prompt` not found** — upgrade: `pip install -U langsmith`.
- **Judge seems wrong** — it's an LLM; show a mis-grade as a teaching moment on why
  you validate the judge itself.
