from __future__ import annotations

from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    # Stub for future user auth/subscriptions.
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")
