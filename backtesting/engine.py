from __future__ import annotations

from dataclasses import dataclass

from paid_trading_bot.core.types import AccountState, AIGateStatus
from paid_trading_bot.risk.engine import RiskEngine
from paid_trading_bot.strategy.entry_logic import evaluate_entry
from paid_trading_bot.strategy.trend_follower import detect_trend


@dataclass(frozen=True)
class BacktestConfig:
    symbol: str
    starting_balance: float = 1000.0
    max_positions: int = 1


@dataclass(frozen=True)
class BacktestResult:
    trade_pnls: list[float]
    equity_curve: list[float]


class BacktestEngine:
    def __init__(self, *, risk_engine: RiskEngine):
        self._risk = risk_engine

    def run(self, *, config: BacktestConfig, candles_1h, candles_5m) -> BacktestResult:
        # Minimal skeleton: demonstrates orchestration shape.
        balance = config.starting_balance
        equity_curve: list[float] = [balance]
        trade_pnls: list[float] = []

        trend = detect_trend(list(candles_1h))

        entry = evaluate_entry(
            ohlcv_5m=list(candles_5m),
            trend_bias=trend,
            ai_gate=AIGateStatus.OPEN,
            current_positions=0,
            max_positions=config.max_positions,
        )

        if entry is None:
            return BacktestResult(trade_pnls=trade_pnls, equity_curve=equity_curve)

        # Pretend 1 trade, flat PnL for now.
        account_state = AccountState(
            balance=balance,
            daily_pnl_percent=0.0,
            current_drawdown_percent=0.0,
            consecutive_losses=0,
            open_positions=0,
            trades_today=0,
        )

        # RiskEngine wiring point; actual TradeRequest construction will be added later.
        _ = self._risk
        _ = account_state

        trade_pnls.append(0.0)
        equity_curve.append(balance)

        return BacktestResult(trade_pnls=trade_pnls, equity_curve=equity_curve)
