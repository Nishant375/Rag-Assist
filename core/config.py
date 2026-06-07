"""
core/config.py

Single source of truth for all configuration.
Every module imports `settings` from here — no scattered os.getenv() calls.

Usage:
    from core.config import settings
    print(settings.groq_model)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",          # loaded in local dev, ignored if file not present
        env_file_encoding="utf-8",
        env_ignore_empty=True,    # cloud containers pass env vars directly — no file needed
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model:   str = "llama-3.1-8b-instant"

    # ── Embedding provider ────────────────────────────────────────────────────
    embed_provider:     str = "ollama"          # ollama | google | openai
    embed_dim:          int = 768

    # Ollama (local)
    ollama_base_url:    str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"

    # Google (free cloud)
    google_api_key:     str = ""
    google_embed_model: str = "models/gemini-embedding-001"

    # OpenAI
    openai_api_key:     str = ""
    openai_embed_model: str = "text-embedding-3-small"

    # ── Vector store ──────────────────────────────────────────────────────────
    vector_store: str = "postgres"              # pinecone | postgres

    # Postgres
    postgres_url: str = ""

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index:   str = "crag-index"
    pinecone_cloud:   str = "aws"
    pinecone_region:  str = "us-east-1"

    # ── Insforge auth ─────────────────────────────────────────────────────────
    insforge_oss_host: str = ""
    insforge_anon_key: str = ""

    # ── Ingestion ─────────────────────────────────────────────────────────────
    chunk_size:    int = 400
    chunk_overlap: int = 80

    # ── App ───────────────────────────────────────────────────────────────────
    api_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Module-level singleton — import this everywhere
settings = get_settings()
