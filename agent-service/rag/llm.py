"""
rag/llm.py

Lazy-loaded LLM client shared across all RAG nodes.
Import `ask()` to make a single-turn LLM call.
"""

from core.config import settings

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        from langchain_groq import ChatGroq
        _llm = ChatGroq(
            model=settings.groq_model,
            temperature=0,
            api_key=settings.groq_api_key,
        )
    return _llm


def ask(prompt: str) -> str:
    """Single-turn LLM call. Returns the text response."""
    return get_llm().invoke(prompt).content.strip()
