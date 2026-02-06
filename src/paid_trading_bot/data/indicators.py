from __future__ import annotations

from collections.abc import Sequence


def calculate_ema(values: Sequence[float], period: int) -> list[float]:
    if period <= 0:
        raise ValueError("period must be > 0")
    if len(values) == 0:
        return []

    k = 2 / (period + 1)
    ema: list[float] = []

    # Seed EMA with SMA of first period (or first value if not enough data)
    if len(values) < period:
        seed = sum(values) / len(values)
        ema.append(seed)
        start_idx = 1
    else:
        seed = sum(values[:period]) / period
        ema = [seed]
        start_idx = period

    prev = ema[-1]
    for v in values[start_idx:]:
        prev = (v - prev) * k + prev
        ema.append(prev)

    return ema


def calculate_rsi(closes: Sequence[float], period: int = 14) -> list[float]:
    if period <= 0:
        raise ValueError("period must be > 0")
    if len(closes) < 2:
        return []

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    if len(gains) < period:
        return []

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi: list[float] = []

    def rs_to_rsi(rs: float) -> float:
        return 100.0 - (100.0 / (1.0 + rs))

    if avg_loss == 0:
        rsi.append(100.0)
    else:
        rsi.append(rs_to_rsi(avg_gain / avg_loss))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi.append(100.0)
        else:
            rsi.append(rs_to_rsi(avg_gain / avg_loss))

    return rsi


def calculate_atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14) -> list[float]:
    if period <= 0:
        raise ValueError("period must be > 0")
    n = min(len(highs), len(lows), len(closes))
    if n < 2:
        return []

    true_ranges: list[float] = []
    for i in range(1, n):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return []

    atr: list[float] = []
    # Wilder's smoothing: seed with SMA
    prev_atr = sum(true_ranges[:period]) / period
    atr.append(prev_atr)

    for tr in true_ranges[period:]:
        prev_atr = (prev_atr * (period - 1) + tr) / period
        atr.append(prev_atr)

    return atr
