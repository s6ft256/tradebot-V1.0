from __future__ import annotations

from paid_trading_bot.core.types import Candle, TrendBias
from paid_trading_bot.data.indicators import calculate_ema


def detect_trend(ohlcv_1h: list[Candle]) -> TrendBias:
    closes = [c.close for c in ohlcv_1h]
    if len(closes) < 2:
        return TrendBias.NEUTRAL

    ema_50 = calculate_ema(closes, period=50)
    ema_200 = calculate_ema(closes, period=200)

    if not ema_50 or not ema_200:
        return TrendBias.NEUTRAL

    latest_ema50 = ema_50[-1]
    latest_ema200 = ema_200[-1]

    threshold = latest_ema200 * 0.005

    if latest_ema50 > latest_ema200 + threshold:
        return TrendBias.BULLISH
    if latest_ema50 < latest_ema200 - threshold:
        return TrendBias.BEARISH
    return TrendBias.NEUTRAL
