from __future__ import annotations

import json

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from paid_trading_bot.persistence.models import AuditLog


class AuditLogger:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log(self, *, component: str, event_type: str, message: str, payload: dict | None = None) -> None:
        payload_json = json.dumps(payload) if payload is not None else None
        stmt = insert(AuditLog).values(
            component=component,
            event_type=event_type,
            message=message,
            payload_json=payload_json,
        )
        await self._session.execute(stmt)
