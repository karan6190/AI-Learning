"""
05 — Pull a prompt from the hub and USE it.

Instead of hard-coding the prompt in your app, you PULL it from the hub at
runtime. Now the prompt and the code are decoupled: someone can improve the
prompt in the UI and your app picks it up — no redeploy, no code change.

Run 04_push_prompt.py first so the prompt exists.
"""
from dotenv import load_dotenv
from langsmith import Client
from langchain_groq import ChatGroq

load_dotenv()
client = Client()

PROMPT_NAME = "qa-answer-prompt"
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


def main():
    # Pull the latest version...
    prompt = client.pull_prompt(PROMPT_NAME)
    print(f"Pulled '{PROMPT_NAME}' (latest).")

    # ...to pin an EXACT version instead, append the commit hash:
    #   prompt = client.pull_prompt("qa-answer-prompt:<commit-hash>")
    # This is how production pins a known-good prompt.

    chain = prompt | llm
    resp = chain.invoke({"question": "What is the capital of France?"})
    print("\nModel answer:", resp.content)
    print("\n-> The prompt text came from the hub, not this file. Change it in the")
    print("   UI, re-run this script, and the behaviour changes with no code edit.")


if __name__ == "__main__":
    main()
