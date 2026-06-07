"""
services/chat.py

Chat business logic — runs the CRAG agent and returns structured results.
No FastAPI/Streamlit imports — pure Python, fully testable.
"""


def run_chat(message: str) -> dict:
    """
    Run the Corrective RAG agent on a user message.

    Returns:
        {
            "answer": str,
            "steps":  list[str],
            "rewritten_question": str | None,
        }
    """
    from agent.graph import crag_graph

    result = crag_graph.invoke({
        "question":            message,
        "original_question":   message,
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
        "rewritten_question":  final_q if final_q != message else None,
    }
