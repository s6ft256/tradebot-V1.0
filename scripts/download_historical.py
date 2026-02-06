from __future__ import annotations

import argparse
import asyncio

from paid_trading_bot.config.settings import settings
from paid_trading_bot.data.ingestion import DataIngestion
from paid_trading_bot.execution.ccxt_adapter import CCXTAdapter, CCXTConfig


async def _run(symbol: str, timeframe: str, limit: int) -> int:
    adapter = CCXTAdapter(
        CCXTConfig(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
            testnet=settings.exchange_testnet,
        )
    )
    ing = DataIngestion(adapter)
    candles = await ing.fetch_candles(symbol=symbol, timeframe=timeframe, limit=limit)
    await adapter.close()

    print({"symbol": symbol, "timeframe": timeframe, "candles": len(candles)})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    return asyncio.run(_run(args.symbol, args.timeframe, args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
