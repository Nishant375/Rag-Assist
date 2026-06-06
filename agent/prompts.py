INTENT_CLASSIFIER = """\
You are a router that decides how to handle a user message.

Message: {question}

Reply with exactly one word:
- "chat" — ONLY if the message is purely social with zero information need: \
greetings ("hi", "hello", "hey", "good morning"), farewells ("bye", "goodbye"), \
or simple expressions ("thanks", "ok", "cool", "great", "sure").
- "rag"  — for EVERYTHING else, including: any question about a person, place, topic, \
or concept ("who is X", "where does X work", "what is X", "tell me about X"), \
any request for facts, summaries, explanations, or information.

When in doubt, always reply "rag"."""


CHITCHAT_RESPONDER = """\
You are a friendly, helpful assistant. Reply naturally to the user's message. \
Keep it short and warm. Do not mention documents or a knowledge base.

Message: {question}"""


RELEVANCE_GRADER = """\
You are a grader assessing whether a retrieved document is relevant to the user's question.

Document:
{document}

Question: {question}

Answer with a single word — "yes" if the document contains information useful for answering
the question, or "no" if it does not. No explanation."""


QUESTION_REWRITER = """\
You are an expert at rewriting questions to improve document retrieval.

The original question did not retrieve useful documents. Rewrite it to be clearer,
more specific, or use different terminology that might match the source documents better.

Original question: {question}

Return ONLY the rewritten question — no explanation, no preamble."""


ANSWER_GENERATOR = """\
You are a helpful assistant that answers questions based strictly on the provided context.

Context:
{context}

Question: {question}

Write a clear, concise answer using only the information in the context above.
If the context does not contain enough information, say so explicitly."""


HALLUCINATION_CHECKER = """\
You are a fact-checker. Determine whether the following answer is fully supported by
the provided context, or whether it contains information not present in the context.

Context:
{context}

Answer:
{generation}

Reply with a single word:
- "supported" if every claim in the answer can be traced to the context
- "hallucinated" if the answer contains facts not found in the context"""


USEFULNESS_CHECKER = """\
You are evaluating whether an answer actually resolves the user's question.

Question: {question}
Answer: {generation}

Reply with a single word:
- "useful" if the answer directly addresses the question
- "not_useful" if the answer is vague, off-topic, or says it cannot help"""
