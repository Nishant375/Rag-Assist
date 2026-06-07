"""
providers/embeddings.py

Returns the correct embedder based on settings.embed_provider.
Swap providers by changing EMBED_PROVIDER in .env — no code changes needed.

Supported values:
  ollama  → Ollama (local, free, default for dev)
  google  → Google gemini-embedding-001 (free cloud, best for Insforge)
  openai  → OpenAI text-embedding-3-small (paid)
"""

from core.config import settings

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder

    provider = settings.embed_provider.lower()

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        _embedder = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        print(f"[embeddings] ollama → {settings.ollama_embed_model}")

    elif provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        _embedder = GoogleGenerativeAIEmbeddings(
            model=settings.google_embed_model,
            google_api_key=settings.google_api_key,
            output_dimensionality=settings.embed_dim,
        )
        print(f"[embeddings] google → {settings.google_embed_model} (dim={settings.embed_dim})")

    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        _embedder = OpenAIEmbeddings(
            model=settings.openai_embed_model,
            openai_api_key=settings.openai_api_key,
        )
        print(f"[embeddings] openai → {settings.openai_embed_model}")

    else:
        raise ValueError(
            f"Unknown EMBED_PROVIDER='{provider}'. Supported: ollama, google, openai"
        )

    return _embedder


def get_embed_dim() -> int:
    return settings.embed_dim
