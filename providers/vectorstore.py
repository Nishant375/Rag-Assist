"""
providers/vectorstore.py

Unified interface for vector storage — swap backends via VECTOR_STORE env var.

Supported values:
  pinecone  → Pinecone serverless (default)
  postgres  → PostgreSQL + pgvector via direct psycopg2 (local Docker / Supabase)
  insforge  → Insforge PostgREST API (no direct DB connection needed — best for Insforge deploy)

All backends expose the same 4 methods:
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


# ── Insforge PostgREST backend ────────────────────────────────────────────────

class InsforgeStore:
    """
    Uses Insforge's REST database API — no direct Postgres connection needed.
    Works from any Fly.io compute service deployed via Insforge.

    For vector similarity search, uses a Postgres function `search_embeddings`
    that we create once via the CLI.

    Required env vars:
      INSFORGE_OSS_HOST  → e.g. https://d3kmwe4w.ap-southeast.insforge.app
      INSFORGE_API_KEY   → e.g. ik_5fb5dfd79044d61e07ac4cbb79d05a5f
    """

    def __init__(self):
        import requests as req
        self._req     = req
        self.base_url = os.environ["INSFORGE_OSS_HOST"].rstrip("/")
        self.api_key  = os.environ["INSFORGE_API_KEY"]
        self.headers  = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }
        print(f"[vectorstore] Connected to Insforge API → {self.base_url}")

    def _records_url(self):
        return f"{self.base_url}/api/database/records/embeddings"

    def _rpc_url(self, fn: str):
        return f"{self.base_url}/api/database/rpc/{fn}"

    def upsert(self, chunks: list[str], embeddings: list[list[float]], source: str):
        """Upsert chunks in batches via the records API."""
        records = [
            {
                "id":        _stable_id(source, i),
                "source":    source,
                "content":   chunk,
                "embedding": str(emb),   # Postgres vector string format
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        # Upsert in batches of 20
        for start in range(0, len(records), 20):
            batch = records[start:start + 20]
            resp  = self._req.post(
                self._records_url(),
                headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                json=batch,
                timeout=60,
            )
            if not resp.ok:
                raise RuntimeError(f"Upsert failed {resp.status_code}: {resp.text[:300]}")

    def search(self, query_vector: list[float], top_k: int = 5) -> list[str]:
        """Call the search_embeddings SQL function for vector similarity search."""
        resp = self._req.post(
            self._rpc_url("search_embeddings"),
            headers=self.headers,
            json={"query_vector": str(query_vector), "match_count": top_k},
            timeout=30,
        )
        if not resp.ok:
            raise RuntimeError(f"Search failed {resp.status_code}: {resp.text[:300]}")
        return [r["content"] for r in resp.json()]

    def list_sources(self) -> list[dict]:
        resp = self._req.get(
            self._records_url(),
            headers=self.headers,
            params={"select": "source", "limit": 10000},
            timeout=15,
        )
        if not resp.ok:
            return []
        rows = resp.json()
        counts: dict[str, int] = {}
        for r in rows:
            counts[r["source"]] = counts.get(r["source"], 0) + 1
        return [
            {"source": src, "chunks": cnt, "store": "insforge"}
            for src, cnt in sorted(counts.items())
        ]

    def delete_source(self, source: str):
        resp = self._req.delete(
            self._records_url(),
            headers=self.headers,
            params={"source": f"eq.{source}"},
            timeout=15,
        )
        if not resp.ok:
            raise RuntimeError(f"Delete failed {resp.status_code}: {resp.text[:200]}")


# ── Factory ───────────────────────────────────────────────────────────────────

def get_vectorstore():
    global _store
    if _store is not None:
        return _store

    if VECTOR_STORE == "pinecone":
        _store = PineconeStore()
    elif VECTOR_STORE == "postgres":
        _store = PostgresStore()
    elif VECTOR_STORE == "insforge":
        _store = InsforgeStore()
    else:
        raise ValueError(
            f"Unknown VECTOR_STORE='{VECTOR_STORE}'. "
            f"Supported: pinecone, postgres, insforge"
        )

    return _store
