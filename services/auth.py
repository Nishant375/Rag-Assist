"""
services/auth.py

All Insforge authentication logic.
No FastAPI/Streamlit imports — pure Python, fully testable.
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
    """Create a new user account. Returns a message dict."""
    resp = requests.post(
        f"{settings.insforge_oss_host}/auth/signup",
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    if not resp.ok:
        raise AuthError(resp.json().get("message", "Signup failed"))
    return {"message": "Account created. Check your email to verify."}


def login(email: str, password: str) -> dict:
    """Sign in and return access token + user info."""
    resp = requests.post(
        f"{settings.insforge_oss_host}/auth/signin",
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
    """Validate a JWT token and return the user. Raises AuthError if invalid."""
    resp = requests.get(
        f"{settings.insforge_oss_host}/auth/user",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    if not resp.ok:
        raise AuthError("Invalid or expired token")
    return resp.json()
