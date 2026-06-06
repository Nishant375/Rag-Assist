"""
CRAG node functions. Each function receives GraphState and returns a partial dict.
All provider choices (embedder, vector store, LLM) are driven by env vars — no code changes needed.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq

from .state import GraphState
from .prompts import (
    INTENT_CLASSIFIER,
    CHITCHAT_RESPONDER,
    RELEVANCE_GRADER,
    QUESTION_REWRITER,
    ANSWER_GENERATOR,
    HALLUCINATION_CHECKER,
    USEFULNESS_CHECKER,
)

# ── Lazy singletons ───────────────────────────────────────────────────────────

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=0,
            api_key=os.environ["GROQ_API_KEY"],
        )
    return _llm

def _get_embedder():
    from providers.embeddings import get_embedder
    return get_embedder()

def _get_store():
    from providers.vectorstore import get_vectorstore
    return get_vectorstore()


TOP_K = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ask(prompt: str) -> str:
    return _get_llm().invoke(prompt).content.strip()


def _retrieve_docs(question: str) -> list[str]:
    vector = _get_embedder().embed_query(question)
    return _get_store().search(vector, top_k=TOP_K)


# ── Nodes ─────────────────────────────────────────────────────────────────────

def classify_intent(state: GraphState) -> dict:
    prompt  = INTENT_CLASSIFIER.format(question=state["question"])
    verdict = _ask(prompt).strip().lower()
    intent  = "chat" if "chat" in verdict else "rag"
    return {"steps": [f"Intent: {intent}"]}


def chitchat(state: GraphState) -> dict:
    prompt = CHITCHAT_RESPONDER.format(question=state["question"])
    return {
        "generation": _ask(prompt),
        "steps": ["Replied as chitchat"],
    }


def route_intent(state: GraphState) -> str:
    last_step = state.get("steps", [""])[-1]
    return "chat" if "chat" in last_step else "rag"


def retrieve(state: GraphState) -> dict:
    docs = _retrieve_docs(state["question"])
    return {
        "documents": docs,
        "steps": [f"Retrieved {len(docs)} chunks for: \"{state['question']}\""],
    }


def grade_documents(state: GraphState) -> dict:
    relevant = []
    for doc in state["documents"]:
        prompt  = RELEVANCE_GRADER.format(document=doc, question=state["question"])
        verdict = _ask(prompt).lower()
        if "yes" in verdict:
            relevant.append(doc)
    kept  = len(relevant)
    total = len(state["documents"])
    return {
        "documents": relevant,
        "steps": [f"Graded documents: {kept}/{total} relevant"],
    }


def rewrite_question(state: GraphState) -> dict:
    prompt       = QUESTION_REWRITER.format(question=state["question"])
    new_question = _ask(prompt)
    attempts     = state.get("retrieval_attempts", 0) + 1
    return {
        "question":           new_question,
        "retrieval_attempts": attempts,
        "steps": [f"Rewrote question (attempt {attempts}): \"{new_question}\""],
    }


def generate(state: GraphState) -> dict:
    context  = "\n\n---\n\n".join(state["documents"])
    prompt   = ANSWER_GENERATOR.format(context=context, question=state["question"])
    attempts = state.get("generation_attempts", 0) + 1
    return {
        "generation":          _ask(prompt),
        "generation_attempts": attempts,
        "steps": [f"Generated answer (attempt {attempts})"],
    }


# ── Conditional edge functions ────────────────────────────────────────────────

def decide_after_grading(state: GraphState) -> str:
    if state["documents"]:
        return "generate"
    if state.get("retrieval_attempts", 0) >= 2:
        return "generate"
    return "rewrite"


def decide_after_generation(state: GraphState) -> str:
    context    = "\n\n---\n\n".join(state["documents"]) if state["documents"] else ""
    generation = state["generation"]

    if context:
        verdict = _ask(HALLUCINATION_CHECKER.format(context=context, generation=generation)).lower()
        if "hallucinated" in verdict:
            return "end" if state.get("generation_attempts", 0) >= 2 else "regenerate"

    verdict = _ask(USEFULNESS_CHECKER.format(
        question=state["original_question"], generation=generation
    )).lower()
    if "not_useful" in verdict:
        return "end" if state.get("retrieval_attempts", 0) >= 2 else "rewrite"

    return "end"
