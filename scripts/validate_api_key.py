from __future__ import annotations

import argparse
import asyncio

from paid_trading_bot.config.settings import settings
from paid_trading_bot.execution.ccxt_adapter import CCXTAdapter, CCXTConfig


async def _run() -> int:
    # Stub: CCXT does not expose a universal API-key permission check.
    # In a real implementation, validate key scopes via Binance-specific endpoint.
    if not settings.binance_api_key or not settings.binance_api_secret:
        raise RuntimeError("BINANCE_API_KEY/BINANCE_API_SECRET not set")

    adapter = CCXTAdapter(
        CCXTConfig(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
            testnet=settings.exchange_testnet,
        )
    )
    await adapter.close()
    print({"status": "ok", "note": "permission check not implemented"})
    return 0


def main() -> int:
    _ = argparse.ArgumentParser()
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
