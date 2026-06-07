"""
auth.py — Insforge authentication helpers for FastAPI.

Provides:
  - /auth/signup   → create account
  - /auth/login    → get JWT token
  - /auth/me       → get current user
  - verify_token() → FastAPI dependency to protect any route
"""

import os
import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

INSFORGE_URL  = os.environ["INSFORGE_OSS_HOST"]
INSFORGE_ANON = os.environ["INSFORGE_ANON_KEY"]

_bearer = HTTPBearer(auto_error=False)


# ── Schemas ───────────────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    email:    str
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_headers():
    return {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {INSFORGE_ANON}",
    }


def verify_token(credentials: HTTPAuthorizationCredentials = Security(_bearer)):
    """
    FastAPI dependency — validates JWT with Insforge and returns the user.
    Add to any route:  user = Depends(verify_token)
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    resp  = requests.get(
        f"{INSFORGE_URL}/auth/user",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    if not resp.ok:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return resp.json()


# ── Route handlers (imported into api.py) ────────────────────────────────────

def signup_handler(req: AuthRequest):
    resp = requests.post(
        f"{INSFORGE_URL}/auth/signup",
        headers=_auth_headers(),
        json={"email": req.email, "password": req.password},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code,
                            detail=resp.json().get("message", "Signup failed"))
    return {"message": "Account created. Check your email to verify."}


def login_handler(req: AuthRequest):
    resp = requests.post(
        f"{INSFORGE_URL}/auth/signin",
        headers=_auth_headers(),
        json={"email": req.email, "password": req.password},
        timeout=10,
    )
    if not resp.ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    data = resp.json()
    return {
        "access_token": data["accessToken"],
        "token_type":   "bearer",
        "user": {
            "id":    data["user"]["id"],
            "email": data["user"]["email"],
        },
    }


def me_handler(user: dict):
    return {"id": user.get("id"), "email": user.get("email")}
