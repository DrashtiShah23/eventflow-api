import os

from fastapi import Header, HTTPException, status

API_KEY = os.getenv("EVENTFLOW_API_KEY", "dev-secret-key")


def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
