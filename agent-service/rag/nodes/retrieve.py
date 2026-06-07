"""
rag/nodes/retrieve.py  —  Step 2: Retrieval

Embeds the question and fetches the top-K most similar chunks
from the vector store (Postgres/pgvector or Pinecone).

Node:
  retrieve  → writes `documents` list to state
"""

from rag.state import GraphState

TOP_K = 5


def retrieve(state: GraphState) -> dict:
    from providers.embeddings import get_embedder
    from providers.vectorstore import get_vectorstore

    query_vector = get_embedder().embed_query(state["question"])
    documents    = get_vectorstore().search(query_vector, top_k=TOP_K)

    return {
        "documents": documents,
        "steps":     [f'Retrieved {len(documents)} chunks for: "{state["question"]}"'],
    }
