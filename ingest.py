"""
ingest.py — Load documents, chunk, embed, store in vector DB.

Embedding provider and vector store are chosen via env vars — no code changes needed:
  EMBED_PROVIDER = ollama | google | openai
  VECTOR_STORE   = pinecone | postgres

Supports:
  python ingest.py --source ./docs
  python ingest.py --drive-folder-id <FOLDER_ID>
"""

import os
import argparse
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", "400"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


# ── Document readers ──────────────────────────────────────────────────────────

def read_local_files(folder: str) -> Generator[tuple[str, str], None, None]:
    readers = {
        ".txt":  lambda p: p.read_text(errors="ignore"),
        ".md":   lambda p: p.read_text(errors="ignore"),
        ".pdf":  _read_pdf,
        ".docx": _read_docx,
    }
    for path in sorted(Path(folder).rglob("*")):
        reader = readers.get(path.suffix.lower())
        if reader is None:
            continue
        text = reader(path)
        if text and text.strip():
            yield str(path), text


def _read_pdf(path: Path) -> str:
    import pypdf
    return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(path)).pages)


def _read_docx(path: Path) -> str:
    from docx import Document
    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def read_google_drive(folder_id: str) -> Generator[tuple[str, str], None, None]:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io

    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"],
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    drive   = build("drive", "v3", credentials=creds)
    results = drive.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id,name,mimeType)"
    ).execute()

    for f in results.get("files", []):
        mime, fid, name = f["mimeType"], f["id"], f["name"]
        try:
            if mime == "application/vnd.google-apps.document":
                data = drive.files().export(fileId=fid, mimeType="text/plain").execute()
                yield name, data.decode("utf-8", errors="ignore")
            elif mime in ("text/plain", "text/markdown"):
                buf = io.BytesIO()
                MediaIoBaseDownload(buf, drive.files().get_media(fileId=fid)).next_chunk()
                yield name, buf.getvalue().decode("utf-8", errors="ignore")
            else:
                print(f"  Skipping unsupported type: {name}")
        except Exception as exc:
            print(f"  Error reading {name}: {exc}")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def ingest(source_iter):
    from providers.embeddings import get_embedder
    from providers.vectorstore import get_vectorstore

    embedder = get_embedder()
    store    = get_vectorstore()
    total    = 0

    for doc_id, text in source_iter:
        fname  = doc_id.split("/")[-1]
        chunks = splitter.split_text(text)
        if not chunks:
            print(f"  {fname} → no usable text, skipped")
            continue

        print(f"  {fname} → {len(chunks)} chunks, embedding …", end="", flush=True)
        embeddings = embedder.embed_documents(chunks)
        store.upsert(chunks, embeddings, source=fname)
        total += len(chunks)
        print(f" ✓ stored")

    print(f"\n✓ Done — {total} chunks stored")


def main():
    parser = argparse.ArgumentParser()
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source",          help="Local folder path")
    group.add_argument("--drive-folder-id", help="Google Drive folder ID")
    args = parser.parse_args()

    if args.source:
        ingest(read_local_files(args.source))
    else:
        ingest(read_google_drive(args.drive_folder_id))


if __name__ == "__main__":
    main()
