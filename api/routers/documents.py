"""
api/routers/documents.py — Knowledge base document management.

Protected:
  GET    /documents         — list all stored documents
  DELETE /documents/{source} — delete a document
"""

from fastapi import APIRouter, HTTPException, Depends
from api.deps import require_user

router = APIRouter(prefix="/documents", tags=["Documents"])


def _store():
    from providers.vectorstore import get_vectorstore
    return get_vectorstore()


@router.get("")
def list_documents(user: dict = Depends(require_user)):
    try:
        return _store().list_sources()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{source}")
def delete_document(source: str, user: dict = Depends(require_user)):
    try:
        _store().delete_source(source)
        return {"deleted": source}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
