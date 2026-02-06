from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestMetrics:
    trades: int
    win_rate: float
    max_drawdown_percent: float


def compute_metrics(*, trade_pnls: list[float], equity_curve: list[float]) -> BacktestMetrics:
    trades = len(trade_pnls)
    wins = len([p for p in trade_pnls if p > 0])
    win_rate = (wins / trades) if trades else 0.0

    peak = float("-inf")
    max_dd = 0.0
    for eq in equity_curve:
        peak = max(peak, eq)
        if peak > 0:
            dd = (peak - eq) / peak * 100.0
            max_dd = max(max_dd, dd)

    return BacktestMetrics(trades=trades, win_rate=win_rate, max_drawdown_percent=max_dd)
