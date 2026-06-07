"""
ui/client.py — API client for the Streamlit UI.

Single place for all HTTP calls to the backend.
Automatically injects the auth token from session state.
"""

import streamlit as st
import requests
from core.config import settings

API_URL = settings.api_url


def _h() -> dict:
    """Auth headers from session state."""
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


# ── Health ────────────────────────────────────────────────────────────────────

def is_online() -> bool:
    try:
        return requests.get(f"{API_URL}/health", timeout=2).ok
    except Exception:
        return False


# ── Auth ──────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> dict:
    resp = requests.post(f"{API_URL}/auth/login",
                         json={"email": email, "password": password}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def signup(email: str, password: str) -> dict:
    resp = requests.post(f"{API_URL}/auth/signup",
                         json={"email": email, "password": password}, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Chat ──────────────────────────────────────────────────────────────────────

def chat(message: str) -> dict:
    resp = requests.post(f"{API_URL}/chat",
                         json={"message": message},
                         headers=_h(), timeout=120)
    resp.raise_for_status()
    return resp.json()


# ── Ingest ────────────────────────────────────────────────────────────────────

def upload_files(uploaded_files) -> dict:
    files = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
             for f in uploaded_files]
    resp = requests.post(f"{API_URL}/ingest/upload",
                         files=files, headers=_h(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def trigger_store(upload_id: str) -> dict:
    resp = requests.post(f"{API_URL}/ingest/store/{upload_id}",
                         headers=_h(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_job(job_id: str) -> dict:
    resp = requests.get(f"{API_URL}/ingest/status/{job_id}",
                        headers=_h(), timeout=5)
    resp.raise_for_status()
    return resp.json()


# ── Documents ─────────────────────────────────────────────────────────────────

def list_documents() -> list[dict]:
    try:
        resp = requests.get(f"{API_URL}/documents", headers=_h(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def delete_document(source: str) -> bool:
    try:
        resp = requests.delete(f"{API_URL}/documents/{source}",
                               headers=_h(), timeout=10)
        return resp.ok
    except Exception:
        return False
