"""
api/main.py — FastAPI application factory.

Run:  uvicorn api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, chat, ingest, documents

app = FastAPI(
    title="Rag-Assist API",
    description="Upload your documents and chat with them — Corrective RAG + Groq + pgvector",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health (public) ───────────────────────────────────────────────────────────

@app.get("/health", tags=["Public"])
def health():
    return {"status": "ok"}


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(documents.router)
