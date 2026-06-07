"""
api/deps.py

Shared FastAPI dependencies — imported by every router that needs them.
"""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth import get_user, AuthError

_bearer = HTTPBearer(auto_error=False)


def require_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """
    Validate the Bearer token and return the authenticated user.
    Raises 401 if missing or invalid.

    Usage in any route:
        @router.get("/me")
        def me(user: dict = Depends(require_user)):
            ...
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return get_user(credentials.credentials)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
