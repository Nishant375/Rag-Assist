from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """State shared across all nodes in the CRAG graph."""

    # The user's current question (may be rewritten)
    question: str

    # Original question — preserved so the UI can show it
    original_question: str

    # Retrieved document chunks from Pinecone
    documents: list[str]

    # The LLM's generated answer
    generation: str

    # How many times we've retried generation (hallucination guard)
    generation_attempts: int

    # How many times we've rewritten + re-retrieved (loop guard)
    retrieval_attempts: int

    # Audit trail shown in the UI sidebar
    steps: Annotated[list[str], lambda a, b: a + b]
