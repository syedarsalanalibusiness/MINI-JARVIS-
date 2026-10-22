"""Optional shared-token protection for public API deployments."""

import secrets

from fastapi import Header, HTTPException

from backend.config import get_settings


def require_backend_token(authorization: str | None = Header(default=None)) -> None:
    """Require a bearer token when BACKEND_API_TOKEN is configured."""
    expected = get_settings().backend_api_token.get_secret_value().strip()
    if not expected:
        return
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="This API request is not authorized.")
