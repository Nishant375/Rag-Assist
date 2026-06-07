"""
api/routers/chat.py — Chat endpoint.

Protected: POST /chat
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.chat import run_chat
from api.deps import require_user

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer:             str
    steps:              list[str]
    rewritten_question: str | None = None


@router.post("", response_model=ChatResponse)
def chat_route(req: ChatRequest, user: dict = Depends(require_user)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        result = run_chat(req.message)
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
