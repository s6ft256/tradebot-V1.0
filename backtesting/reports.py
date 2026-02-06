from __future__ import annotations

from dataclasses import asdict

from backtesting.metrics import BacktestMetrics


def render_summary(*, metrics: BacktestMetrics) -> dict:
    return asdict(metrics)
