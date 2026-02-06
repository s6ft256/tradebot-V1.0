from __future__ import annotations

import time

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    def __init__(self, *, max_requests: int = 60, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._hits: dict[str, list[float]] = {}

    async def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self._window
        hits = [t for t in self._hits.get(key, []) if t >= window_start]
        hits.append(now)
        self._hits[key] = hits

        if len(hits) > self._max:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
