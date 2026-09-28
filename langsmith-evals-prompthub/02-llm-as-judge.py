"""
02 — LLM-as-judge evaluation.

The idea: instead of exact string matching (brittle — "Paris" vs "The capital
is Paris." would fail), we ask a SECOND LLM to act as a judge and score whether
the answer is correct. This is "LLM-as-judge".

Flow:
  - TARGET   : our app answers each question in the dataset.
  - JUDGE    : an LLM compares the app's answer to the reference and returns
               correct=true/false with a reason.
  - evaluate(): runs the target over every example, scores each with the judge,
               and logs an EXPERIMENT to LangSmith you can browse.

Run 01_create_dataset.py first.
"""
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import evaluate

load_dotenv()

DATASET_NAME = "qa-eval-demo"

# The app under test
app_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# The judge (kept separate so you can use a stronger/independent model if you like)
judge_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


# ---- TARGET: the thing we are evaluating -----------------------------------
def target(inputs: dict) -> dict:
    """Answer the question. `inputs` matches the dataset's input keys."""
    resp = app_llm.invoke([HumanMessage(content=inputs["question"])])
    return {"answer": resp.content}


# ---- JUDGE: an LLM decides if the answer is correct ------------------------
class Grade(BaseModel):
    correct: bool = Field(description="Is the answer factually correct?")
    reason: str = Field(description="One short sentence explaining the verdict.")


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """LLM-as-judge evaluator. Returns a score LangSmith records on the run."""
    judge = judge_llm.with_structured_output(Grade)
    verdict = judge.invoke([
        SystemMessage(content=(
            "You are a strict grader. Decide if the STUDENT answer is correct "
            "given the REFERENCE answer. Ignore wording/format differences; judge "
            "only factual correctness."
        )),
        HumanMessage(content=(
            f"QUESTION: {inputs['question']}\n"
            f"REFERENCE: {reference_outputs['answer']}\n"
            f"STUDENT: {outputs['answer']}"
        )),
    ])
    return {"key": "correctness", "score": int(verdict.correct), "comment": verdict.reason}


def main():
    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[correctness],
        experiment_prefix="qa-baseline",
    )
    print("Evaluation complete.")
    print("-> Open LangSmith -> Datasets & Testing -> qa-eval-demo -> Experiments.")
    print("   Each row: the question, the app answer, and the judge's score + reason.")


if __name__ == "__main__":
    main()
