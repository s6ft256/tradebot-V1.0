from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.5


class OrderManager:
    def __init__(self, retry_policy: RetryPolicy | None = None):
        self._policy = retry_policy or RetryPolicy()

    async def with_retries(self, fn, *args, **kwargs):
        attempt = 0
        last_exc: Exception | None = None

        while attempt < self._policy.max_attempts:
            attempt += 1
            try:
                return await fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                last_exc = e
                if attempt >= self._policy.max_attempts:
                    raise
                await asyncio.sleep(self._policy.backoff_seconds * attempt)

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("order retries exhausted")
