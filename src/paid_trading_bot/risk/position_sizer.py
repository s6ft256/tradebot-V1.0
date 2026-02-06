from __future__ import annotations

from paid_trading_bot.risk.limits import HardRiskLimits


def calculate_position_size(
    *,
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
    ai_risk_multiplier: float = 1.0,
    hard_limits: HardRiskLimits | None = None,
) -> float:
    limits = hard_limits or HardRiskLimits()

    if account_balance <= 0:
        return 0.0

    risk_percent_capped = min(risk_percent, limits.max_risk_per_trade_percent)
    risk_percent_capped = max(risk_percent_capped, 0.0)

    effective_risk_percent = risk_percent_capped * min(max(ai_risk_multiplier, 0.0), 1.0)
    if effective_risk_percent <= 0:
        return 0.0

    stop_distance = abs(entry_price - stop_loss_price)
    if stop_distance <= 0:
        return 0.0

    risk_amount = account_balance * (effective_risk_percent / 100.0)
    position_size = risk_amount / stop_distance

    if position_size < 0:
        return 0.0
    return position_size
