"""
04 — Errors in a trace.

When a step raises, the run is marked FAILED (red) and the exception + stack
trace are attached to the span. This is how you debug production incidents:
the failing inputs and error are right there — no local repro needed.

We trigger two kinds of failure:
  A) an exception inside a traced tool
  B) a bad model name -> provider error on the LLM span
"""
from dotenv import load_dotenv
from langsmith import traceable
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()


@traceable(run_type="tool", name="divide_metric")
def divide_metric(numerator: float, denominator: float) -> float:
    # Classic bug: denominator can be 0. The trace captures inputs (0!) + traceback.
    return numerator / denominator


def failure_a():
    print("Failure A: exception inside a traced tool (division by zero)")
    try:
        divide_metric(100, 0)
    except ZeroDivisionError as e:
        print(f"  raised: {e} -> see the FAILED tool span in LangSmith\n")


def failure_b():
    print("Failure B: provider error on the LLM span (invalid model)")
    bad_llm = ChatGroq(model="this-model-does-not-exist", temperature=0)
    try:
        bad_llm.invoke([HumanMessage(content="hello")])
    except Exception as e:
        print(f"  raised: {type(e).__name__} -> see the red LLM span with the error\n")


def main():
    failure_a()
    failure_b()
    print("-> In LangSmith, filter the project by Status = Error to find these fast.")


if __name__ == "__main__":
    main()
