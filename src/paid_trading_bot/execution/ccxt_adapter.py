from __future__ import annotations

from dataclasses import dataclass

import ccxt.async_support as ccxt


@dataclass(frozen=True)
class CCXTConfig:
    exchange_id: str = "binance"
    api_key: str | None = None
    api_secret: str | None = None
    testnet: bool = True
    enable_rate_limit: bool = True


class CCXTAdapter:
    def __init__(self, config: CCXTConfig):
        self._config = config
        self._exchange = getattr(ccxt, config.exchange_id)(
            {
                "apiKey": config.api_key,
                "secret": config.api_secret,
                "enableRateLimit": config.enable_rate_limit,
            }
        )

        if config.testnet and hasattr(self._exchange, "set_sandbox_mode"):
            self._exchange.set_sandbox_mode(True)

    async def close(self) -> None:
        await self._exchange.close()

    async def fetch_ohlcv(self, *, symbol: str, timeframe: str, limit: int) -> list[list[float]]:
        return await self._exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    async def create_order(
        self,
        *,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
        params: dict | None = None,
    ):
        return await self._exchange.create_order(
            symbol=symbol,
            type=order_type,
            side=side,
            amount=amount,
            price=price,
            params=params or {},
        )
