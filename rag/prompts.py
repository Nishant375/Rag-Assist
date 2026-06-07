"""
rag/prompts.py

Every prompt used in the RAG pipeline lives here.
Change prompt behaviour → edit this file only, nothing else.

Each prompt is a plain string with {placeholder} variables filled at runtime.
"""

# ── Step 1: Intent ─────────────────────────────────────────────────────────────
# Decides whether to run RAG or reply as chitchat.

INTENT_CLASSIFIER = """\
You are a router. Decide how to handle the user's message.

Message: {question}

Reply with exactly one word:
- "chat" — ONLY for purely social messages with zero information need:
  greetings ("hi", "hello", "hey"), farewells ("bye"), simple expressions
  ("thanks", "ok", "cool", "great").
- "rag"  — for EVERYTHING else: any question about a person, place, topic,
  or concept ("who is X", "where does X work", "what is X", "explain X"),
  any request for facts, summaries, or information.

When in doubt → reply "rag"."""

CHITCHAT_RESPONDER = """\
You are a friendly, helpful assistant. Reply naturally to the user's message.
Keep it short and warm. Do not mention documents or a knowledge base.

Message: {question}"""


# ── Step 3: Grade ──────────────────────────────────────────────────────────────
# Judges whether a retrieved chunk actually helps answer the question.

RELEVANCE_GRADER = """\
You are grading whether a document chunk is useful for answering a question.

Document:
{document}

Question: {question}

Reply with ONE word:
- "yes" if the document contains information relevant to the question
- "no"  if it does not

No explanation."""


# ── Step 4: Rewrite ────────────────────────────────────────────────────────────
# Improves the question when retrieval found nothing useful.

QUESTION_REWRITER = """\
You are an expert at improving search queries.

The question below did not retrieve useful documents. Rewrite it to be clearer,
more specific, or use different terminology that better matches source documents.

Original question: {question}

Return ONLY the rewritten question — no explanation, no preamble."""


# ── Step 5: Generate ───────────────────────────────────────────────────────────
# Produces the final answer from retrieved context.

ANSWER_GENERATOR = """\
You are a helpful assistant that answers questions using only the provided context.

Context:
{context}

Question: {question}

Write a clear, concise answer using only the information above.
If the context does not contain enough information, say so explicitly."""


# ── Step 6a: Hallucination check ──────────────────────────────────────────────
# Verifies the answer is grounded in the retrieved documents.

HALLUCINATION_CHECKER = """\
You are a fact-checker. Determine whether the answer below is fully supported
by the provided context, or contains claims not found there.

Context:
{context}

Answer:
{generation}

Reply with ONE word:
- "supported"    — every claim in the answer can be traced to the context
- "hallucinated" — the answer contains facts not present in the context"""


# ── Step 6b: Usefulness check ─────────────────────────────────────────────────
# Verifies the answer actually addresses the user's question.

USEFULNESS_CHECKER = """\
Does the answer actually resolve the user's question?

Question: {question}
Answer:   {generation}

Reply with ONE word:
- "useful"     — the answer directly addresses the question
- "not_useful" — the answer is vague, off-topic, or unhelpful"""
