"""
services/chat.py

Chat service — thin wrapper around the RAG pipeline.
The service layer doesn't know how RAG works internally.
"""

from rag.pipeline import ask


def run_chat(message: str) -> dict:
    """
    Run the Corrective RAG pipeline on a user message.

    Returns:
        {
            "answer":             str
            "steps":              list[str]
            "rewritten_question": str | None
        }
    """
    return ask(message)
