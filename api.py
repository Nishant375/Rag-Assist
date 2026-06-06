"""
api.py — FastAPI backend for the CRAG agent.

Endpoints:
  POST /chat                    — send a message, get an answer
  POST /ingest/upload           — upload files + start ingestion job
  GET  /ingest/status/{job_id}  — poll job progress
  GET  /ingest/jobs             — list all past jobs
  GET  /health                  — liveness check
"""

import os
import uuid
import asyncio
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from agent.graph import crag_graph

app = FastAPI(
    title="Corrective RAG API",
    description="CRAG agent — LangGraph + Groq + Ollama + Pinecone",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ── In-memory job store ───────────────────────────────────────────────────────

jobs: dict[str, dict] = {}


def new_job(folder: str, filenames: list[str]) -> str:
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "id":           job_id,
        "folder":       folder,
        "filenames":    filenames,
        "status":       "queued",
        "started_at":   datetime.now(timezone.utc).isoformat(),
        "finished_at":  None,
        "files_found":  len(filenames),
        "files_done":   0,
        "chunks_total": 0,
        "current_file": None,
        "log":          [],
        "error":        None,
    }
    return job_id


def job_log(job_id: str, msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    jobs[job_id]["log"].append(f"[{ts}] {msg}")


# ── Background ingestion ──────────────────────────────────────────────────────

async def run_ingestion(job_id: str, folder: str):
    from ingest import splitter, _read_pdf, _read_docx
    from providers.embeddings import get_embedder
    from providers.vectorstore import get_vectorstore

    j = jobs[job_id]
    j["status"] = "running"
    job_log(job_id, "Job started")

    try:
        embedder = get_embedder()
        store    = get_vectorstore()
        job_log(job_id, f"Providers ready ✓")

        files = list(Path(folder).iterdir())
        j["files_found"] = len(files)
        job_log(job_id, f"Processing {len(files)} file(s) …")

        for i, path in enumerate(files, 1):
            fname = path.name
            j["current_file"] = fname
            job_log(job_id, f"[{i}/{len(files)}] {fname}")

            if path.suffix.lower() == ".pdf":
                text = _read_pdf(path)
            elif path.suffix.lower() == ".docx":
                text = _read_docx(path)
            else:
                text = path.read_text(errors="ignore")

            chunks = splitter.split_text(text)
            if not chunks:
                job_log(job_id, f"  ↳ no text found, skipped")
                j["files_done"] += 1
                continue

            job_log(job_id, f"  ↳ {len(chunks)} chunks — embedding …")
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, embedder.embed_documents, chunks
            )

            store.upsert(chunks, embeddings, source=fname)
            j["chunks_total"] += len(chunks)
            j["files_done"]   += 1
            job_log(job_id, f"  ↳ stored {len(chunks)} chunks ✓")

        j["current_file"] = None
        j["status"]       = "done"
        j["finished_at"]  = datetime.now(timezone.utc).isoformat()
        job_log(job_id, f"All done — {j['chunks_total']:,} chunks stored ✓")

    except Exception as exc:
        j["status"]      = "failed"
        j["error"]       = str(exc)
        j["finished_at"] = datetime.now(timezone.utc).isoformat()
        job_log(job_id, f"ERROR: {exc}")

    finally:
        shutil.rmtree(folder, ignore_errors=True)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    steps: list[str]
    rewritten_question: str | None = None

class IngestStarted(BaseModel):
    job_id:  str
    files:   list[str]
    message: str = "Ingestion started. Poll /ingest/status/{job_id} for progress."


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")
    try:
        result = crag_graph.invoke({
            "question":            req.message,
            "original_question":   req.message,
            "documents":           [],
            "generation":          "",
            "generation_attempts": 0,
            "retrieval_attempts":  0,
            "steps":               [],
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    final_q = result.get("question", "")
    return ChatResponse(
        answer=result.get("generation") or "I could not find a relevant answer.",
        steps=result.get("steps", []),
        rewritten_question=final_q if final_q != req.message else None,
    )


@app.post("/ingest/upload")
async def ingest_upload(files: list[UploadFile] = File(...)):
    """Step 1 — Save uploaded files. Does NOT start ingestion yet."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    upload_id     = str(uuid.uuid4())[:8]
    upload_folder = UPLOAD_DIR / upload_id
    upload_folder.mkdir(parents=True)

    filenames = []
    for upload in files:
        dest = upload_folder / upload.filename
        dest.write_bytes(await upload.read())
        filenames.append(upload.filename)

    return {
        "upload_id": upload_id,
        "files":     filenames,
        "message":   f"{len(filenames)} file(s) uploaded. Call POST /ingest/store/{upload_id} to start ingestion.",
    }


@app.post("/ingest/store/{upload_id}", response_model=IngestStarted)
def ingest_store(upload_id: str, background_tasks: BackgroundTasks):
    """Step 2 — Trigger embedding + Pinecone storage for a previous upload."""
    folder = UPLOAD_DIR / upload_id
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"Upload '{upload_id}' not found. Upload files first.")

    filenames = [f.name for f in folder.iterdir()]
    if not filenames:
        raise HTTPException(status_code=400, detail="Upload folder is empty.")

    job_id = new_job(str(folder), filenames)
    background_tasks.add_task(run_ingestion, job_id, str(folder))

    return IngestStarted(job_id=job_id, files=filenames)


@app.get("/ingest/status/{job_id}")
def ingest_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/ingest/jobs")
def list_jobs():
    return sorted(jobs.values(), key=lambda j: j["started_at"], reverse=True)


@app.get("/documents")
def list_documents():
    """List all unique source files stored in the vector DB with chunk counts."""
    from providers.vectorstore import get_vectorstore
    try:
        return get_vectorstore().list_sources()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/documents/{source}")
def delete_document(source: str):
    """Delete all chunks for a given source file from the vector DB."""
    from providers.vectorstore import get_vectorstore
    try:
        get_vectorstore().delete_source(source)
        return {"deleted": source}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
