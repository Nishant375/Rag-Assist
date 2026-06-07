"""
rag/nodes/check.py  —  Step 6: Answer quality checks

Two sequential checks after generation:

  1. Hallucination check  — is every claim in the answer supported by the
     retrieved documents? If not, regenerate.

  2. Usefulness check — does the answer actually address the question?
     If not and retries remain, rewrite the question and try again.

Edge function:
  route_after_check  → "end" | "regenerate" | "rewrite"
"""

from rag.state import GraphState
from rag.llm import ask
from rag.prompts import HALLUCINATION_CHECKER, USEFULNESS_CHECKER

MAX_GENERATION_ATTEMPTS = 2
MAX_RETRIEVAL_ATTEMPTS  = 2


def route_after_check(state: GraphState) -> str:
    """
    Runs both checks and returns the next routing decision.

    Returns:
      "end"        — answer is good, return it to the user
      "regenerate" — answer is hallucinated, try generating again
      "rewrite"    — answer is not useful, rewrite question and retrieve again
    """
    context    = "\n\n---\n\n".join(state["documents"]) if state["documents"] else ""
    generation = state["generation"]

    # ── Check 1: Hallucination ─────────────────────────────────────────────
    if context:
        verdict = ask(HALLUCINATION_CHECKER.format(
            context=context, generation=generation
        )).lower()

        if "hallucinated" in verdict:
            if state.get("generation_attempts", 0) >= MAX_GENERATION_ATTEMPTS:
                return "end"   # give up after max attempts
            return "regenerate"

    # ── Check 2: Usefulness ────────────────────────────────────────────────
    verdict = ask(USEFULNESS_CHECKER.format(
        question=state["original_question"], generation=generation
    )).lower()

    if "not_useful" in verdict:
        if state.get("retrieval_attempts", 0) >= MAX_RETRIEVAL_ATTEMPTS:
            return "end"   # give up after max attempts
        return "rewrite"

    return "end"
