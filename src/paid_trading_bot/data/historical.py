from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from paid_trading_bot.persistence.database import Base


@dataclass(frozen=True)
class HistoricalCandle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str


class HistoricalCandleModel(Base):
    """SQLAlchemy model for storing historical OHLCV data."""

    __tablename__ = "historical_candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("idx_candle_lookup", "symbol", "timeframe", "timestamp"),
        Index("idx_candle_time", "timestamp"),
    )

    @classmethod
    def from_candle(cls, candle: HistoricalCandle) -> "HistoricalCandleModel":
        return cls(
            symbol=candle.symbol,
            timeframe=candle.timeframe,
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )


class CandleRepository:
    """Repository for historical candle data operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_candles(self, candles: list[HistoricalCandle]) -> int:
        """Save multiple candles, ignoring duplicates."""
        if not candles:
            return 0

        models = [HistoricalCandleModel.from_candle(c) for c in candles]
        self._session.add_all(models)
        await self._session.flush()
        return len(models)

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[HistoricalCandle]:
        """Retrieve candles within a time range."""
        start = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start
        end = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end

        result = await self._session.execute(
            select(HistoricalCandleModel)
            .where(HistoricalCandleModel.symbol == symbol)
            .where(HistoricalCandleModel.timeframe == timeframe)
            .where(HistoricalCandleModel.timestamp >= start)
            .where(HistoricalCandleModel.timestamp <= end)
            .order_by(HistoricalCandleModel.timestamp)
            .limit(limit)
        )

        return [
            HistoricalCandle(
                timestamp=m.timestamp,
                open=m.open,
                high=m.high,
                low=m.low,
                close=m.close,
                volume=m.volume,
                symbol=m.symbol,
                timeframe=m.timeframe,
            )
            for m in result.scalars().all()
        ]

    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[HistoricalCandle]:
        """Get the most recent candle for a symbol/timeframe."""
        result = await self._session.execute(
            select(HistoricalCandleModel)
            .where(HistoricalCandleModel.symbol == symbol)
            .where(HistoricalCandleModel.timeframe == timeframe)
            .order_by(HistoricalCandleModel.timestamp.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return HistoricalCandle(
            timestamp=model.timestamp,
            open=model.open,
            high=model.high,
            low=model.low,
            close=model.close,
            volume=model.volume,
            symbol=model.symbol,
            timeframe=model.timeframe,
        )

    async def delete_old_candles(self, symbol: str, timeframe: str, before: datetime) -> int:
        """Delete candles older than a given timestamp."""
        from sqlalchemy import delete

        before = before.replace(tzinfo=timezone.utc) if before.tzinfo is None else before

        result = await self._session.execute(
            delete(HistoricalCandleModel)
            .where(HistoricalCandleModel.symbol == symbol)
            .where(HistoricalCandleModel.timeframe == timeframe)
            .where(HistoricalCandleModel.timestamp < before)
        )
        return result.rowcount or 0
