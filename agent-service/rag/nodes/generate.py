"""
rag/nodes/generate.py  —  Step 5: Answer generation

Joins all relevant chunks into a context string and asks the LLM
to write a grounded answer. The answer must be based only on the
provided context — hallucination is caught by the check node next.

Node:
  generate  → writes `generation` to state, increments attempt counter
"""

from rag.state import GraphState
from rag.llm import ask
from rag.prompts import ANSWER_GENERATOR


def generate(state: GraphState) -> dict:
    context  = "\n\n---\n\n".join(state["documents"]) if state["documents"] else ""
    answer   = ask(ANSWER_GENERATOR.format(
        context=context, question=state["question"]
    ))
    attempts = state.get("generation_attempts", 0) + 1
    return {
        "generation":          answer,
        "generation_attempts": attempts,
        "steps": [f"Generated answer (attempt {attempts})"],
    }
