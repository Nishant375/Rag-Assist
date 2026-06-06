"""
providers/embeddings.py

Returns the correct embedder based on EMBED_PROVIDER env var.

Supported values:
  ollama  → Ollama (local, free, default for dev)
  google  → Google text-embedding-004 (free cloud)
  openai  → OpenAI text-embedding-3-small (paid)

Usage:
  from providers.embeddings import get_embedder
  embedder = get_embedder()
"""

import os

EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "ollama").lower()
EMBED_DIM_MAP  = {
    "ollama": 768,
    "google": 768,
    "openai": 1536,
}
EMBED_DIM = int(os.getenv("EMBED_DIM", str(EMBED_DIM_MAP.get(EMBED_PROVIDER, 768))))

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder

    if EMBED_PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings
        _embedder = OllamaEmbeddings(
            model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
        print(f"[embeddings] Using Ollama → {os.getenv('OLLAMA_EMBED_MODEL','nomic-embed-text')}")

    elif EMBED_PROVIDER == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        _embedder = GoogleGenerativeAIEmbeddings(
            model=os.getenv("GOOGLE_EMBED_MODEL", "models/gemini-embedding-001"),
            google_api_key=os.environ["GOOGLE_API_KEY"],
            output_dimensionality=int(os.getenv("EMBED_DIM", "768")),
        )
        print(f"[embeddings] Using Google → {os.getenv('GOOGLE_EMBED_MODEL','models/gemini-embedding-001')} (dim={os.getenv('EMBED_DIM','768')})")

    elif EMBED_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        _embedder = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
            openai_api_key=os.environ["OPENAI_API_KEY"],
        )
        print(f"[embeddings] Using OpenAI → {os.getenv('OPENAI_EMBED_MODEL','text-embedding-3-small')}")

    else:
        raise ValueError(
            f"Unknown EMBED_PROVIDER='{EMBED_PROVIDER}'. "
            f"Supported: ollama, google, openai"
        )

    return _embedder


def get_embed_dim() -> int:
    return EMBED_DIM
