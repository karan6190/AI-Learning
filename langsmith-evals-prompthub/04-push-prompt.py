"""
04 — Push a prompt to the LangSmith PROMPT HUB.

Problem this solves: prompts usually live hard-coded in random .py files. Nobody
knows the "current" version, changes aren't tracked, and non-engineers can't edit
them. The Prompt Hub is a version-controlled home for prompts — like Git, but for
prompts, with a UI anyone can use.

This script pushes a prompt. Each push creates a new COMMIT (version) you can see
in the UI. Run 06 to push a second version and watch the history grow.

After running, open LangSmith -> Prompts -> 'qa-answer-prompt'.
"""
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
client = Client()

PROMPT_NAME = "qa-answer-prompt"

# A prompt template with a {question} variable
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer the question concisely."),
    ("human", "{question}"),
])


def main():
    url = client.push_prompt(PROMPT_NAME, object=prompt)
    print(f"Pushed prompt '{PROMPT_NAME}'.")
    print(f"View it here: {url}")
    print("-> In LangSmith -> Prompts, open it and note the commit hash (the version).")


if __name__ == "__main__":
    main()
