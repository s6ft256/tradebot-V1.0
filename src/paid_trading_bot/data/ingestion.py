from __future__ import annotations

from datetime import datetime, timezone

from paid_trading_bot.core.types import Candle
from paid_trading_bot.execution.ccxt_adapter import CCXTAdapter


def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)


class DataIngestion:
    def __init__(self, adapter: CCXTAdapter):
        self._adapter = adapter

    async def fetch_candles(self, *, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        rows = await self._adapter.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        candles: list[Candle] = []
        for ts, o, h, l, c, v in rows:
            candles.append(
                Candle(
                    timestamp=_ms_to_dt(int(ts)),
                    open=float(o),
                    high=float(h),
                    low=float(l),
                    close=float(c),
                    volume=float(v),
                )
            )
        return candles
