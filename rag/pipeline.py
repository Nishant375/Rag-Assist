"""
rag/pipeline.py

Public API for the RAG pipeline. Import this from services, never import
individual nodes or graph internals directly.

Usage:
    from rag.pipeline import ask

    result = ask("Who is Nishant?")
    print(result["answer"])
    print(result["steps"])
"""

from rag.graph import get_graph


def ask(question: str) -> dict:
    """
    Run the full Corrective RAG pipeline on a question.

    Args:
        question: The user's message (any language)

    Returns:
        {
            "answer":             str   — the final answer
            "steps":              list  — audit trail of what each node did
            "rewritten_question": str | None — if the question was rewritten
        }
    """
    result  = get_graph().invoke({
        "question":            question,
        "original_question":   question,
        "documents":           [],
        "generation":          "",
        "generation_attempts": 0,
        "retrieval_attempts":  0,
        "steps":               [],
    })

    final_q = result.get("question", "")
    return {
        "answer":              result.get("generation") or "I could not find a relevant answer.",
        "steps":               result.get("steps", []),
        "rewritten_question":  final_q if final_q != question else None,
    }
