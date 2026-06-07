"""
rag/nodes/grade.py  —  Step 3: Document grading

Asks the LLM whether each retrieved chunk is actually relevant
to the question. Keeps only the relevant ones.

Node:
  grade_documents  → filters `documents`, writes count to steps

Edge function:
  route_after_grade  → "generate" if relevant docs exist, "rewrite" if not
"""

from rag.state import GraphState
from rag.llm import ask
from rag.prompts import RELEVANCE_GRADER

MAX_RETRIEVAL_ATTEMPTS = 2


def grade_documents(state: GraphState) -> dict:
    relevant = [
        doc for doc in state["documents"]
        if "yes" in ask(RELEVANCE_GRADER.format(
            document=doc, question=state["question"]
        )).lower()
    ]
    kept  = len(relevant)
    total = len(state["documents"])
    return {
        "documents": relevant,
        "steps":     [f"Graded: {kept}/{total} chunks relevant"],
    }


def route_after_grade(state: GraphState) -> str:
    """
    Edge: if we have relevant docs → generate.
    If not and retries remain → rewrite question and try again.
    If retries exhausted → generate with whatever we have (or empty context).
    """
    if state["documents"]:
        return "generate"
    if state.get("retrieval_attempts", 0) >= MAX_RETRIEVAL_ATTEMPTS:
        return "generate"   # best-effort answer
    return "rewrite"
