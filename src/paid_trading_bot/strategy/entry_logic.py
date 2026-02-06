from __future__ import annotations

from paid_trading_bot.core.types import AIGateStatus, Candle, EntrySignal, TradeSide, TrendBias
from paid_trading_bot.data.indicators import calculate_atr, calculate_ema, calculate_rsi


def evaluate_entry(
    *,
    ohlcv_5m: list[Candle],
    trend_bias: TrendBias,
    ai_gate: AIGateStatus,
    current_positions: int,
    max_positions: int,
) -> EntrySignal | None:
    if ai_gate != AIGateStatus.OPEN:
        return None

    if trend_bias == TrendBias.NEUTRAL:
        return None

    if current_positions >= max_positions:
        return None

    closes = [c.close for c in ohlcv_5m]
    highs = [c.high for c in ohlcv_5m]
    lows = [c.low for c in ohlcv_5m]

    ema_20 = calculate_ema(closes, period=20)
    rsi = calculate_rsi(closes, period=14)
    atr = calculate_atr(highs, lows, closes, period=14)

    if not ema_20 or not rsi or not atr:
        return None

    current_price = closes[-1]
    current_ema20 = ema_20[-1]
    current_rsi = rsi[-1]
    current_atr = atr[-1]

    pullback_threshold = current_ema20 * 0.003
    is_near_ema = abs(current_price - current_ema20) < pullback_threshold

    if not is_near_ema:
        return None

    if trend_bias == TrendBias.BULLISH:
        if current_rsi > 45 and current_price > current_ema20:
            return EntrySignal(
                side=TradeSide.LONG,
                entry_price=current_price,
                stop_loss=current_price - (1.5 * current_atr),
                take_profit_1=current_price + (1.5 * current_atr),
                take_profit_2=current_price + (3.0 * current_atr),
                atr=current_atr,
            )

    if trend_bias == TrendBias.BEARISH:
        if current_rsi < 55 and current_price < current_ema20:
            return EntrySignal(
                side=TradeSide.SHORT,
                entry_price=current_price,
                stop_loss=current_price + (1.5 * current_atr),
                take_profit_1=current_price - (1.5 * current_atr),
                take_profit_2=current_price - (3.0 * current_atr),
                atr=current_atr,
            )

    return None
