"""
rag/nodes/rewrite.py  —  Step 4: Question rewriting

When retrieval returns no useful chunks, this node asks the LLM
to rephrase the question with better terminology so the next
retrieval attempt has a higher chance of finding relevant content.

Node:
  rewrite_question  → replaces `question` in state, increments retry counter
"""

from rag.state import GraphState
from rag.llm import ask
from rag.prompts import QUESTION_REWRITER


def rewrite_question(state: GraphState) -> dict:
    new_question = ask(QUESTION_REWRITER.format(question=state["question"]))
    attempts     = state.get("retrieval_attempts", 0) + 1
    return {
        "question":           new_question,
        "retrieval_attempts": attempts,
        "steps": [f'Rewrote question (attempt {attempts}): "{new_question}"'],
    }
