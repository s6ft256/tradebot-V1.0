from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HardRiskLimits:
    max_risk_per_trade_percent: float = 1.0
    min_risk_per_trade_percent: float = 0.5
    daily_loss_cap_percent: float = 3.0
    max_drawdown_percent: float = 10.0
    max_consecutive_losses: int = 5
    max_open_positions: int = 2
    max_trades_per_day: int = 6
    max_slippage_percent: float = 0.5
    api_key_withdrawal_check: bool = True
