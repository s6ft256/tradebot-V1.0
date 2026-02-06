from datetime import datetime, timedelta

from paid_trading_bot.core.types import AIGateStatus, Candle, TrendBias
from paid_trading_bot.strategy.entry_logic import evaluate_entry


def _candles_up(n: int, start: float = 100.0, step: float = 0.05) -> list[Candle]:
    now = datetime.utcnow()
    candles: list[Candle] = []
    price = start
    for i in range(n):
        ts = now - timedelta(minutes=(n - i) * 5)
        o = price
        c = price + step
        h = max(o, c) + 0.02
        l = min(o, c) - 0.02
        candles.append(Candle(timestamp=ts, open=o, high=h, low=l, close=c, volume=1.0))
        price = c
    return candles


def test_entry_returns_none_when_gate_closed():
    candles = _candles_up(120)
    sig = evaluate_entry(
        ohlcv_5m=candles,
        trend_bias=TrendBias.BULLISH,
        ai_gate=AIGateStatus.COOLDOWN,
        current_positions=0,
        max_positions=2,
    )
    assert sig is None
