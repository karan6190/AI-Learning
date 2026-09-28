"""
03 — Compare TWO prompts with the same judge (the payoff).

This is why evals matter: you change a prompt and want to PROVE it's better,
not just feel it. We run the same dataset + same judge against two different
system prompts, producing two experiments you can compare side-by-side in
LangSmith.

This also sets up the Prompt Hub lesson: "which prompt version scored better?"

Run 01_create_dataset.py first.
"""
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import evaluate

load_dotenv()

DATASET_NAME = "qa-eval-demo"
app_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
judge_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# Two competing prompts — the thing we're comparing
PROMPT_V1 = "Answer the question."
PROMPT_V2 = ("Answer the question with ONLY the exact fact requested — no full "
             "sentences, no extra words. Example: Q 'Capital of Japan?' A 'Tokyo'.")


def make_target(system_prompt: str):
    def target(inputs: dict) -> dict:
        resp = app_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=inputs["question"]),
        ])
        return {"answer": resp.content}
    return target


class Grade(BaseModel):
    correct: bool = Field(description="Is the answer factually correct?")
    reason: str = Field(description="One short sentence explaining the verdict.")


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    judge = judge_llm.with_structured_output(Grade)
    verdict = judge.invoke([
        SystemMessage(content="Judge factual correctness only. Ignore wording/format."),
        HumanMessage(content=(
            f"QUESTION: {inputs['question']}\n"
            f"REFERENCE: {reference_outputs['answer']}\n"
            f"STUDENT: {outputs['answer']}"
        )),
    ])
    return {"key": "correctness", "score": int(verdict.correct), "comment": verdict.reason}


def main():
    print("Running experiment for PROMPT_V1 ...")
    evaluate(make_target(PROMPT_V1), data=DATASET_NAME,
             evaluators=[correctness], experiment_prefix="prompt-v1")

    print("Running experiment for PROMPT_V2 ...")
    evaluate(make_target(PROMPT_V2), data=DATASET_NAME,
             evaluators=[correctness], experiment_prefix="prompt-v2")

    print("\nBoth experiments done.")
    print("-> In LangSmith, open the dataset -> Experiments, tick both runs,")
    print("   and click Compare. You'll see per-example scores side by side.")


if __name__ == "__main__":
    main()
