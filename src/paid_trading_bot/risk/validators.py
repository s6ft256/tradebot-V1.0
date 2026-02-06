from __future__ import annotations

from dataclasses import dataclass

from paid_trading_bot.core.types import AccountState, TradeRequest
from paid_trading_bot.risk.limits import HardRiskLimits


@dataclass(frozen=True)
class ValidationResult:
    approved: bool
    reason: str
    details: str


def calculate_trade_risk_percent(
    *,
    position_size: float,
    entry_price: float,
    stop_loss: float,
    account_balance: float,
) -> float:
    if account_balance <= 0:
        return 0.0

    stop_distance = abs(entry_price - stop_loss)
    if stop_distance <= 0:
        return 0.0

    risk_amount = position_size * stop_distance
    return (risk_amount / account_balance) * 100.0


def validate_trade_request(
    *,
    request: TradeRequest,
    account_state: AccountState,
    risk_limits: HardRiskLimits,
) -> ValidationResult:
    if account_state.daily_pnl_percent <= -risk_limits.daily_loss_cap_percent:
        return ValidationResult(
            approved=False,
            reason="DAILY_LOSS_CAP_HIT",
            details=f"Daily loss {account_state.daily_pnl_percent}% exceeds cap",
        )

    if account_state.current_drawdown_percent >= risk_limits.max_drawdown_percent:
        return ValidationResult(
            approved=False,
            reason="MAX_DRAWDOWN_HIT",
            details=f"Drawdown {account_state.current_drawdown_percent}% exceeds limit",
        )

    if account_state.consecutive_losses >= risk_limits.max_consecutive_losses:
        return ValidationResult(
            approved=False,
            reason="MAX_CONSECUTIVE_LOSSES_HIT",
            details=f"{account_state.consecutive_losses} consecutive losses",
        )

    if account_state.open_positions >= risk_limits.max_open_positions:
        return ValidationResult(
            approved=False,
            reason="MAX_POSITIONS_REACHED",
            details=f"{account_state.open_positions} positions already open",
        )

    if account_state.trades_today >= risk_limits.max_trades_per_day:
        return ValidationResult(
            approved=False,
            reason="MAX_DAILY_TRADES_REACHED",
            details=f"{account_state.trades_today} trades executed today",
        )

    trade_risk_percent = calculate_trade_risk_percent(
        position_size=request.position_size,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        account_balance=account_state.balance,
    )

    if trade_risk_percent > risk_limits.max_risk_per_trade_percent:
        return ValidationResult(
            approved=False,
            reason="RISK_PER_TRADE_EXCEEDED",
            details=(
                f"Trade risk {trade_risk_percent}% exceeds {risk_limits.max_risk_per_trade_percent}%"
            ),
        )

    return ValidationResult(
        approved=True,
        reason="ALL_CHECKS_PASSED",
        details="OK",
    )
