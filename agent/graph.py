"""
Builds and compiles the Corrective RAG LangGraph.

Flow:
               START
                 │
        ┌────────▼────────┐
        │ classify_intent │
        └────────┬────────┘
         "chat" / "rag"
           │         │
    ┌──────▼──┐  ┌───▼──────┐
    │ chitchat│  │ retrieve  │
    └──────┬──┘  └───┬──────┘
           │         │
          END  ┌─────▼──────────┐
               │ grade_documents │
               └─────┬──────────┘
        relevant?    │    none relevant
      ┌──────────────┼──────────────┐
  "generate"     "rewrite"    (max retries → generate)
      │               │
      │    ┌──────────▼──────┐
      │    │ rewrite_question │
      │    └──────────┬──────┘
      │               │ (loops back to retrieve)
  ┌───▼────┐
  │generate│
  └───┬────┘
      │
  decide_after_generation
      │
  "end" → END  |  "regenerate" → generate  |  "rewrite" → rewrite_question
"""

from langgraph.graph import StateGraph, END

from .state import GraphState
from .nodes import (
    classify_intent,
    chitchat,
    route_intent,
    retrieve,
    grade_documents,
    rewrite_question,
    generate,
    decide_after_grading,
    decide_after_generation,
)


def build_graph():
    g = StateGraph(GraphState)

    # ── Nodes ─────────────────────────────────────────────────────────────────
    g.add_node("classify_intent",   classify_intent)
    g.add_node("chitchat",          chitchat)
    g.add_node("retrieve",          retrieve)
    g.add_node("grade_documents",   grade_documents)
    g.add_node("rewrite_question",  rewrite_question)
    g.add_node("generate",          generate)

    # ── Edges ─────────────────────────────────────────────────────────────────
    g.set_entry_point("classify_intent")

    g.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "chat": "chitchat",
            "rag":  "retrieve",
        },
    )

    g.add_edge("chitchat", END)
    g.add_edge("retrieve", "grade_documents")

    g.add_conditional_edges(
        "grade_documents",
        decide_after_grading,
        {
            "generate": "generate",
            "rewrite":  "rewrite_question",
        },
    )

    g.add_edge("rewrite_question", "retrieve")

    g.add_conditional_edges(
        "generate",
        decide_after_generation,
        {
            "end":        END,
            "regenerate": "generate",
            "rewrite":    "rewrite_question",
        },
    )

    return g.compile()


# Singleton — imported by app
crag_graph = build_graph()
