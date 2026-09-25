"""
03 — Token usage & cost.

Every LLM span records prompt/completion/total tokens. We also show @traceable so
a plain Python function becomes its own span.

In the UI:
  - Open a run -> the LLM span shows token counts on the right.
  - Project view -> columns for tokens, aggregated across runs.

(Note: Groq/gpt-oss is open-source; LangSmith may not show a $ cost since there's
no fixed public price, but token counts are always captured.)
"""
from dotenv import load_dotenv
from langsmith import traceable
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


@traceable(run_type="chain", name="ask_three_ways")
def ask_three_ways(topic: str):
    """One traced function, three child LLM calls of different sizes."""
    prompts = [
        f"Define '{topic}' in 5 words.",
        f"Explain '{topic}' in one paragraph.",
        f"Write a 300-word explainer on '{topic}' with examples.",
    ]
    answers = []
    for p in prompts:
        resp = llm.invoke([HumanMessage(content=p)])
        answers.append(resp.content)
    return answers


def main():
    answers = ask_three_ways("token usage in LLM tracing")
    for i, a in enumerate(answers, 1):
        print(f"--- answer {i} ---\n{a}\n")
    print("-> Compare the 3 LLM spans' token counts. Bigger prompt/output = more tokens.")
    print("-> Project view aggregates total tokens across all runs.")


if __name__ == "__main__":
    main()
