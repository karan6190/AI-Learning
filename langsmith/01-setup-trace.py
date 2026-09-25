"""
01 — Setup & your first trace.

Run this, then open https://smith.langchain.com -> project 'langsmith-demo'
and open the newest run. Everything below was auto-instrumented just because
LANGSMITH_TRACING=true was set in the environment.
"""
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()  # loads LANGSMITH_* and GROQ_API_KEY from .env

# gpt-oss open model, served by Groq
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


def main():
    resp = llm.invoke([HumanMessage(content="In one sentence, what is LangSmith?")])
    print(resp.content)
    print("\n-> Open LangSmith and look at the run: inputs, outputs, model, timing.")


if __name__ == "__main__":
    main()
