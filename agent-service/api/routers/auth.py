"""
api/routers/auth.py — Authentication endpoints.

Public:    POST /auth/signup   POST /auth/login
Protected: GET  /auth/me
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.auth import signup, login, AuthError
from api.deps import require_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthRequest(BaseModel):
    email:    str
    password: str


@router.post("/signup")
def signup_route(req: AuthRequest):
    try:
        return signup(req.email, req.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login_route(req: AuthRequest):
    try:
        return login(req.email, req.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
def me_route(user: dict = Depends(require_user)):
    return {"id": user.get("id"), "email": user.get("email")}
