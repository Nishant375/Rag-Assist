"""
rag/state.py

The single data structure that flows through every node in the RAG graph.
Each node receives the full state and returns only the keys it changes.
LangGraph merges the partial dict back automatically.

Flow:
  question → intent → retrieve → grade → [rewrite → retrieve → grade]* → generate → check → answer
"""

from typing import Annotated
from typing_extensions import TypedDict


class GraphState(TypedDict):
    # The user's current question (may be rewritten by the rewrite node)
    question: str

    # Preserved original — used in usefulness check and UI display
    original_question: str

    # Chunks retrieved from the vector store
    documents: list[str]

    # The LLM-generated answer
    generation: str

    # Guards against infinite regeneration loops
    generation_attempts: int

    # Guards against infinite rewrite + retrieve loops
    retrieval_attempts: int

    # Audit trail — each node appends one line describing what it did
    # The `Annotated` + lambda ensures lists are merged, not replaced
    steps: Annotated[list[str], lambda a, b: a + b]
