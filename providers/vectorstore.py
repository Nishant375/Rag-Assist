"""
providers/vectorstore.py

Unified interface for vector storage — swap backends via VECTOR_STORE env var.

Supported values:
  pinecone  → Pinecone serverless (default)
  postgres  → PostgreSQL + pgvector (works with Insforge, Supabase, or any Postgres)

Both backends expose the same 4 methods:
  upsert(chunks, embeddings, source)   → store chunks
  search(query_vector, top_k)          → return list of text strings
  list_sources()                       → return [{source, chunk_count, store}]
  delete_source(source)                → remove all chunks from a doc

Usage:
  from providers.vectorstore import get_vectorstore
  vs = get_vectorstore()
  vs.upsert(chunks, embeddings, source="report.pdf")
  results = vs.search(query_vector, top_k=5)
"""

import os
import hashlib

VECTOR_STORE = os.getenv("VECTOR_STORE", "pinecone").lower()

_store = None


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _stable_id(source: str, chunk_index: int) -> str:
    h = hashlib.md5(source.encode()).hexdigest()[:8]
    return f"{h}::{chunk_index}"


# ── Pinecone backend ───────────────────────────────────────────────────────────

class PineconeStore:
    def __init__(self):
        from pinecone import Pinecone, ServerlessSpec
        from providers.embeddings import get_embed_dim

        pc  = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        idx = os.getenv("PINECONE_INDEX", "crag-index")

        existing = [i.name for i in pc.list_indexes()]
        if idx not in existing:
            print(f"[vectorstore] Creating Pinecone index '{idx}' …")
            pc.create_index(
                name=idx,
                dimension=get_embed_dim(),
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=os.getenv("PINECONE_CLOUD", "aws"),
                    region=os.getenv("PINECONE_REGION", "us-east-1"),
                ),
            )
        self.index = pc.Index(idx)
        print(f"[vectorstore] Connected to Pinecone → {idx}")

    def upsert(self, chunks: list[str], embeddings: list[list[float]], source: str):
        vectors = [
            {
                "id":       _stable_id(source, i),
                "values":   emb,
                "metadata": {"source": source, "text": chunk},
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        for start in range(0, len(vectors), 100):
            self.index.upsert(vectors=vectors[start:start + 100])

    def search(self, query_vector: list[float], top_k: int = 5) -> list[str]:
        results = self.index.query(
            vector=query_vector, top_k=top_k, include_metadata=True
        )
        return [m["metadata"]["text"] for m in results["matches"]]

    def list_sources(self) -> list[dict]:
        """Return all unique sources with their chunk counts."""
        stats = self.index.describe_index_stats()
        total = stats.get("total_vector_count", 0)
        if total == 0:
            return []

        # Fetch a large sample of vectors and group by source metadata
        # (Pinecone free tier doesn't support metadata-only queries)
        result  = self.index.query(
            vector=[0.0] * self.index.describe_index_stats()["dimension"],
            top_k=min(total, 10000),
            include_metadata=True,
        )
        counts: dict[str, int] = {}
        for match in result["matches"]:
            src = match.get("metadata", {}).get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1

        return [
            {"source": src, "chunks": cnt, "store": "pinecone"}
            for src, cnt in sorted(counts.items())
        ]

    def delete_source(self, source: str):
        ids = [_stable_id(source, i) for i in range(10000)]
        # Delete in batches of 1000 (Pinecone limit)
        for i in range(0, len(ids), 1000):
            self.index.delete(ids=ids[i:i+1000])


# ── Postgres + pgvector backend ───────────────────────────────────────────────

class PostgresStore:
    def __init__(self):
        import psycopg2
        from providers.embeddings import get_embed_dim

        self.conn_str = os.environ["POSTGRES_URL"]   # postgres://user:pass@host:5432/db
        self.dim      = get_embed_dim()
        self._init_table()
        print(f"[vectorstore] Connected to Postgres + pgvector (dim={self.dim})")

    def _conn(self):
        import psycopg2
        return psycopg2.connect(self.conn_str)

    def _init_table(self):
        """Create the pgvector extension and embeddings table if they don't exist."""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id        TEXT PRIMARY KEY,
                    source    TEXT NOT NULL,
                    content   TEXT NOT NULL,
                    embedding vector({self.dim}) NOT NULL
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS embeddings_source_idx
                ON embeddings (source);
            """)
            # Use hnsw index — works well at any data size, no lists tuning needed
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS embeddings_vector_idx
                ON embeddings USING hnsw (embedding vector_cosine_ops);
            """)
            conn.commit()

    def upsert(self, chunks: list[str], embeddings: list[list[float]], source: str):
        with self._conn() as conn, conn.cursor() as cur:
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                cur.execute("""
                    INSERT INTO embeddings (id, source, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    ON CONFLICT (id) DO UPDATE
                        SET content   = EXCLUDED.content,
                            embedding = EXCLUDED.embedding;
                """, (_stable_id(source, i), source, chunk, str(emb)))
            conn.commit()

    def search(self, query_vector: list[float], top_k: int = 5) -> list[str]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT content
                FROM   embeddings
                ORDER  BY embedding <=> %s::vector
                LIMIT  %s;
            """, (str(query_vector), top_k))
            return [row[0] for row in cur.fetchall()]

    def list_sources(self) -> list[dict]:
        """Return all unique sources with their chunk counts."""
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT source, COUNT(*) as chunks
                FROM   embeddings
                GROUP  BY source
                ORDER  BY source;
            """)
            return [
                {"source": row[0], "chunks": row[1], "store": "postgres"}
                for row in cur.fetchall()
            ]

    def delete_source(self, source: str):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM embeddings WHERE source = %s;", (source,))
            conn.commit()


# ── Factory ───────────────────────────────────────────────────────────────────

def get_vectorstore():
    global _store
    if _store is not None:
        return _store

    if VECTOR_STORE == "pinecone":
        _store = PineconeStore()
    elif VECTOR_STORE == "postgres":
        _store = PostgresStore()
    else:
        raise ValueError(
            f"Unknown VECTOR_STORE='{VECTOR_STORE}'. "
            f"Supported: pinecone, postgres"
        )

    return _store
