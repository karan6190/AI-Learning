"""
02 — Reading latency.

We build a small chain with multiple steps and add an artificial slow step so
the waterfall in LangSmith clearly shows WHERE time went. In the UI open the run
and look at the timeline / waterfall: each span shows its own duration.
"""
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


def slow_preprocess(text: str) -> str:
    """Deliberately slow — you'll see this span dominate the waterfall."""
    time.sleep(2.0)
    return text.strip()


prompt = ChatPromptTemplate.from_template("Summarise this for a 5-year-old:\n\n{topic}")

# named steps -> named spans in the trace
chain = (
    RunnableLambda(slow_preprocess).with_config(run_name="slow_preprocess")
    | (lambda t: {"topic": t})
    | prompt
    | llm
    | StrOutputParser()
)


def main():
    out = chain.invoke("Distributed tracing for LLM applications")
    print(out)
    print("\n-> In LangSmith, open the run's waterfall. 'slow_preprocess' ~2s,")
    print("   the LLM call is the rest. This is how you find the slow step.")


if __name__ == "__main__":
    main()
