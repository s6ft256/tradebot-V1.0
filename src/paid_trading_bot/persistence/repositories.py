from __future__ import annotations

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from paid_trading_bot.persistence.models import EncryptedAPIKey, Trade


class TradeRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_trade(self, *, symbol: str, side: str, qty: float, price: float, status: str) -> int:
        stmt = insert(Trade).values(symbol=symbol, side=side, qty=qty, price=price, status=status).returning(Trade.id)
        res = await self._session.execute(stmt)
        trade_id = res.scalar_one()
        return int(trade_id)


class APIKeyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_key(
        self,
        *,
        user_id: str,
        exchange: str,
        api_key_ciphertext_b64: str,
        api_secret_ciphertext_b64: str,
    ) -> int:
        stmt = insert(EncryptedAPIKey).values(
            user_id=user_id,
            exchange=exchange,
            api_key_ciphertext_b64=api_key_ciphertext_b64,
            api_secret_ciphertext_b64=api_secret_ciphertext_b64,
        ).returning(EncryptedAPIKey.id)
        res = await self._session.execute(stmt)
        key_id = res.scalar_one()
        return int(key_id)

    async def get_key(self, *, user_id: str, exchange: str) -> EncryptedAPIKey | None:
        stmt = select(EncryptedAPIKey).where(
            EncryptedAPIKey.user_id == user_id,
            EncryptedAPIKey.exchange == exchange,
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()
