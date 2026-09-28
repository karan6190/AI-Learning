"""
01 — Create an evaluation DATASET in LangSmith.

An eval needs three things:
  1. a DATASET   — example inputs (+ optional reference/"gold" answers)
  2. a TARGET    — the app/prompt you want to test (script 02)
  3. EVALUATORS  — how you score the output (script 02: an LLM judge)

This script builds the dataset once. Re-running it is safe — it skips creation
if the dataset already exists.

After running, open LangSmith -> Datasets & Testing -> 'qa-eval-demo'.
"""
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()
client = Client()

DATASET_NAME = "qa-eval-demo"

# input = the question we send; output = the reference ("gold") answer we judge against
EXAMPLES = [
    {"question": "What is the capital of France?", "answer": "Paris"},
    {"question": "What is 2 + 2?", "answer": "4"},
    {"question": "Who wrote Romeo and Juliet?", "answer": "William Shakespeare"},
    {"question": "What is the boiling point of water at sea level in Celsius?",
     "answer": "100 degrees Celsius"},
    {"question": "What planet is known as the Red Planet?", "answer": "Mars"},
]


def main():
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Dataset '{DATASET_NAME}' already exists — skipping.")
        return

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Tiny QA set for teaching LLM-as-judge evals.",
    )
    client.create_examples(
        dataset_id=dataset.id,
        inputs=[{"question": e["question"]} for e in EXAMPLES],
        outputs=[{"answer": e["answer"]} for e in EXAMPLES],
    )
    print(f"Created dataset '{DATASET_NAME}' with {len(EXAMPLES)} examples.")
    print("-> Open LangSmith -> Datasets & Testing to see it.")


if __name__ == "__main__":
    main()
