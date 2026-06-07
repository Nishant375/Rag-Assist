"""
rag/graph.py

Wires all RAG nodes into a LangGraph state machine.

Full flow diagram:

  START
    │
    ▼
  classify_intent ──► "chat" ──► chitchat ──► END
    │
   "rag"
    │
    ▼
  retrieve
    │
    ▼
  grade_documents
    │
    ├─ relevant docs found ──────────────────────────────────┐
    │                                                         │
    └─ no relevant docs                                       │
          │                                                   ▼
          ├─ retries left ──► rewrite_question ──► retrieve  generate
          │                        (loop)                     │
          └─ retries exhausted ────────────────────────────►  │
                                                              ▼
                                                        route_after_check
                                                              │
                                           ┌──────────────────┼──────────────────┐
                                          "end"          "regenerate"          "rewrite"
                                           │                  │                   │
                                          END             generate          rewrite_question
"""

from functools import lru_cache
from langgraph.graph import StateGraph, END

from rag.state import GraphState
from rag.nodes.intent   import classify_intent, chitchat, route_intent
from rag.nodes.retrieve import retrieve
from rag.nodes.grade    import grade_documents, route_after_grade
from rag.nodes.rewrite  import rewrite_question
from rag.nodes.generate import generate
from rag.nodes.check    import route_after_check


def build_graph():
    g = StateGraph(GraphState)

    # ── Register nodes ────────────────────────────────────────────────────────
    g.add_node("classify_intent",   classify_intent)
    g.add_node("chitchat",          chitchat)
    g.add_node("retrieve",          retrieve)
    g.add_node("grade_documents",   grade_documents)
    g.add_node("rewrite_question",  rewrite_question)
    g.add_node("generate",          generate)

    # ── Wire edges ────────────────────────────────────────────────────────────
    g.set_entry_point("classify_intent")

    g.add_conditional_edges(
        "classify_intent", route_intent,
        {"chat": "chitchat", "rag": "retrieve"},
    )

    g.add_edge("chitchat",  END)
    g.add_edge("retrieve",  "grade_documents")

    g.add_conditional_edges(
        "grade_documents", route_after_grade,
        {"generate": "generate", "rewrite": "rewrite_question"},
    )

    g.add_edge("rewrite_question", "retrieve")   # loop back

    g.add_conditional_edges(
        "generate", route_after_check,
        {"end": END, "regenerate": "generate", "rewrite": "rewrite_question"},
    )

    return g.compile()


@lru_cache(maxsize=1)
def get_graph():
    """Singleton — compiled once, reused for every request."""
    return build_graph()
