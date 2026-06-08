"""
api/routers/ingest.py — Document ingestion endpoints.

Protected:
  POST /ingest/upload           — save files, return upload_id
  POST /ingest/store/{upload_id} — embed + store in vector DB, return job_id
  GET  /ingest/status/{job_id}  — poll job progress
  GET  /ingest/jobs             — list all jobs
"""

import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Depends
from pydantic import BaseModel

from services.ingest import ingest_folder_async
from api.deps import require_user

router     = APIRouter(prefix="/ingest", tags=["Ingest"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory job store — swap for Redis/DB in production
_jobs: dict[str, dict] = {}


def _new_job(folder: str, filenames: list[str]) -> str:
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "id":           job_id,
        "folder":       folder,
        "filenames":    filenames,
        "status":       "queued",
        "started_at":   datetime.now(timezone.utc).isoformat(),
        "finished_at":  None,
        "files_found":  len(filenames),
        "files_done":   0,
        "files_stored": 0,
        "chunks_total": 0,
        "current_file": None,
        "skipped":      [],
        "log":          [],
        "error":        None,
    }
    return job_id


def _log(job_id: str, msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    _jobs[job_id]["log"].append(f"[{ts}] {msg}")


async def _run_job(job_id: str, folder: str):
    try:
        await ingest_folder_async(
            folder=folder,
            job=_jobs[job_id],
            log=lambda msg: _log(job_id, msg),
        )
    finally:
        _jobs[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
        shutil.rmtree(folder, ignore_errors=True)


class IngestStarted(BaseModel):
    job_id:  str
    files:   list[str]
    message: str = "Ingestion started. Poll /ingest/status/{job_id} for progress."


@router.post("/upload")
async def upload(
    files: list[UploadFile] = File(...),
    user:  dict = Depends(require_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    upload_id     = str(uuid.uuid4())[:8]
    upload_folder = UPLOAD_DIR / upload_id
    upload_folder.mkdir(parents=True)

    filenames = []
    for f in files:
        (upload_folder / f.filename).write_bytes(await f.read())
        filenames.append(f.filename)

    return {"upload_id": upload_id, "files": filenames,
            "message": f"{len(filenames)} file(s) uploaded."}


@router.post("/store/{upload_id}", response_model=IngestStarted)
def store(
    upload_id:        str,
    background_tasks: BackgroundTasks,
    user:             dict = Depends(require_user),
):
    folder = UPLOAD_DIR / upload_id
    if not folder.exists():
        raise HTTPException(status_code=404, detail="Upload not found.")

    filenames = [f.name for f in folder.iterdir()]
    if not filenames:
        raise HTTPException(status_code=400, detail="Upload folder is empty.")

    job_id = _new_job(str(folder), filenames)
    background_tasks.add_task(_run_job, job_id, str(folder))
    return IngestStarted(job_id=job_id, files=filenames)


@router.get("/status/{job_id}")
def status(job_id: str, user: dict = Depends(require_user)):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


@router.get("/jobs")
def list_jobs(user: dict = Depends(require_user)):
    return sorted(_jobs.values(), key=lambda j: j["started_at"], reverse=True)
