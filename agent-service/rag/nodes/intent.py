"""
rag/nodes/intent.py  —  Step 1: Intent classification

Decides whether the user message needs document retrieval (rag)
or can be answered directly as casual conversation (chat).

Nodes:
  classify_intent  → reads question, writes intent to steps
  chitchat         → replies directly without touching vector store

Edge function:
  route_intent     → returns "chat" or "rag" for conditional routing
"""

from rag.state import GraphState
from rag.llm import ask
from rag.prompts import INTENT_CLASSIFIER, CHITCHAT_RESPONDER


def classify_intent(state: GraphState) -> dict:
    verdict = ask(INTENT_CLASSIFIER.format(question=state["question"])).lower()
    intent  = "chat" if "chat" in verdict else "rag"
    return {"steps": [f"Intent → {intent}"]}


def chitchat(state: GraphState) -> dict:
    answer = ask(CHITCHAT_RESPONDER.format(question=state["question"]))
    return {
        "generation": answer,
        "steps":      ["Replied as chitchat (no retrieval needed)"],
    }


def route_intent(state: GraphState) -> str:
    """Edge: send to 'chitchat' or 'retrieve' based on last step."""
    return "chat" if "chat" in (state.get("steps") or [""])[-1] else "rag"
