"""
services/auth.py

Insforge authentication using the correct REST API endpoints:
  POST /api/auth/users    — register
  POST /api/auth/sessions — login
  GET  /api/auth/me       — get current user from token
"""

import requests
from core.config import settings


class AuthError(Exception):
    pass


def _headers() -> dict:
    return {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {settings.insforge_anon_key}",
    }


def signup(email: str, password: str) -> dict:
    """Create a new user account."""
    resp = requests.post(
        f"{settings.insforge_oss_host}/api/auth/users?client_type=server",
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    if not resp.ok:
        body = resp.json() if resp.content else {}
        raise AuthError(body.get("message", f"Signup failed ({resp.status_code})"))
    return {"message": "Account created. Check your email to verify, then log in."}


def login(email: str, password: str) -> dict:
    """Sign in and return access token + user info."""
    resp = requests.post(
        f"{settings.insforge_oss_host}/api/auth/sessions?client_type=server",
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    if not resp.ok:
        raise AuthError("Invalid email or password")

    data = resp.json()
    return {
        "access_token": data["accessToken"],
        "token_type":   "bearer",
        "user": {
            "id":    data["user"]["id"],
            "email": data["user"]["email"],
        },
    }


def get_user(token: str) -> dict:
    """Validate a JWT and return the user. Raises AuthError if invalid."""
    resp = requests.get(
        f"{settings.insforge_oss_host}/api/auth/sessions/current",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    if not resp.ok:
        raise AuthError("Invalid or expired token")
    data = resp.json()
    # Response shape: { user: { id, email, ... }, accessToken, ... }
    return data.get("user", data)
