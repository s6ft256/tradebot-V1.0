from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
import time

if TYPE_CHECKING:
    from paid_trading_bot.core.types import Position, TradeRequest


@dataclass
class SafetyConstraintResult:
    """Result of safety constraint check."""
    passed: bool
    constraint_name: str
    message: str
    severity: str = "warning"  # info, warning, critical


@dataclass
class TradingSession:
    """Tracks trading session statistics."""
    start_time: datetime = field(default_factory=datetime.utcnow)
    trades_today: int = 0
    daily_pnl: float = 0.0
    consecutive_losses: int = 0
    last_trade_time: datetime | None = None
    position_history: list[dict] = field(default_factory=list)


class SafetyConstraints:
    """
    Comprehensive safety constraints for trading bot.
    Mandatory for paid trading bot operations.
    """

    def __init__(
        self,
        max_trades_per_day: int = 6,
        max_consecutive_losses: int = 5,
        daily_loss_cap_percent: float = 3.0,
        max_drawdown_percent: float = 10.0,
        min_time_between_trades_seconds: int = 300,
        max_position_hold_hours: int = 72,
        forbidden_symbols: list[str] | None = None,
        max_correlation_exposure: float = 0.5,
    ):
        self._max_trades_per_day = max_trades_per_day
        self._max_consecutive_losses = max_consecutive_losses
        self._daily_loss_cap = daily_loss_cap_percent
        self._max_drawdown = max_drawdown_percent
        self._min_time_between_trades = min_time_between_trades_seconds
        self._max_position_hold = max_position_hold_hours
        self._forbidden_symbols = set(forbidden_symbols or [])
        self._max_correlation = max_correlation_exposure
        self._session = TradingSession()
        self._position_start_times: dict[str, datetime] = {}

    def check_all_constraints(
        self,
        request: TradeRequest,
        open_positions: list[Position],
        account_balance: float,
        current_drawdown: float,
    ) -> list[SafetyConstraintResult]:
        """Run all safety constraint checks."""
        results = []
        
        results.append(self._check_daily_trade_limit())
        results.append(self._check_time_between_trades())
        results.append(self._check_consecutive_losses())
        results.append(self._check_daily_loss_cap())
        results.append(self._check_drawdown(current_drawdown))
        results.append(self._check_symbol_allowed(request.symbol))
        results.append(self._check_position_limit(open_positions))
        results.append(self._check_correlation_exposure(request.symbol, open_positions))
        results.append(self._check_account_balance(request, account_balance))
        results.append(self._check_position_size(request, account_balance))
        
        return results

    def _check_daily_trade_limit(self) -> SafetyConstraintResult:
        """Check if daily trade limit exceeded."""
        self._reset_daily_if_needed()
        
        if self._session.trades_today >= self._max_trades_per_day:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="daily_trade_limit",
                message=f"Daily trade limit reached: {self._session.trades_today}/{self._max_trades_per_day}",
                severity="critical",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="daily_trade_limit",
            message=f"Trades today: {self._session.trades_today}/{self._max_trades_per_day}",
            severity="info",
        )

    def _check_time_between_trades(self) -> SafetyConstraintResult:
        """Enforce minimum time between trades."""
        if self._session.last_trade_time is None:
            return SafetyConstraintResult(
                passed=True,
                constraint_name="time_between_trades",
                message="First trade of session",
                severity="info",
            )
        
        elapsed = (datetime.utcnow() - self._session.last_trade_time).total_seconds()
        if elapsed < self._min_time_between_trades:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="time_between_trades",
                message=f"Wait {self._min_time_between_trades - elapsed:.0f}s before next trade",
                severity="warning",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="time_between_trades",
            message=f"Time since last trade: {elapsed:.0f}s",
            severity="info",
        )

    def _check_consecutive_losses(self) -> SafetyConstraintResult:
        """Check consecutive loss streak."""
        if self._session.consecutive_losses >= self._max_consecutive_losses:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="consecutive_losses",
                message=f"Consecutive loss limit: {self._session.consecutive_losses}/{self._max_consecutive_losses}. Trading paused.",
                severity="critical",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="consecutive_losses",
            message=f"Consecutive losses: {self._session.consecutive_losses}/{self._max_consecutive_losses}",
            severity="info",
        )

    def _check_daily_loss_cap(self) -> SafetyConstraintResult:
        """Check daily loss cap."""
        self._reset_daily_if_needed()
        
        if self._session.daily_pnl <= -self._daily_loss_cap:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="daily_loss_cap",
                message=f"Daily loss cap hit: {self._session.daily_pnl:.2f}% (limit: -{self._daily_loss_cap}%)",
                severity="critical",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="daily_loss_cap",
            message=f"Daily P&L: {self._session.daily_pnl:.2f}% (cap: -{self._daily_loss_cap}%)",
            severity="info",
        )

    def _check_drawdown(self, current_drawdown: float) -> SafetyConstraintResult:
        """Check maximum drawdown."""
        if current_drawdown >= self._max_drawdown:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="max_drawdown",
                message=f"Max drawdown exceeded: {current_drawdown:.2f}% (limit: {self._max_drawdown}%)",
                severity="critical",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="max_drawdown",
            message=f"Current drawdown: {current_drawdown:.2f}% (limit: {self._max_drawdown}%)",
            severity="info",
        )

    def _check_symbol_allowed(self, symbol: str) -> SafetyConstraintResult:
        """Check if symbol is in forbidden list."""
        if symbol in self._forbidden_symbols:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="symbol_allowed",
                message=f"Symbol {symbol} is forbidden",
                severity="critical",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="symbol_allowed",
            message=f"Symbol {symbol} allowed",
            severity="info",
        )

    def _check_position_limit(self, open_positions: list[Position]) -> SafetyConstraintResult:
        """Check maximum open positions."""
        # Note: actual limit checked by RiskEngine, this is additional safety
        if len(open_positions) >= 2:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="position_limit",
                message=f"Maximum positions reached: {len(open_positions)}",
                severity="warning",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="position_limit",
            message=f"Open positions: {len(open_positions)}/2",
            severity="info",
        )

    def _check_correlation_exposure(
        self,
        new_symbol: str,
        open_positions: list[Position],
    ) -> SafetyConstraintResult:
        """Check correlation exposure (avoid over-concentration)."""
        crypto_pairs = {"BTC/USD", "BTC/USDT", "ETH/USD", "ETH/USDT"}
        forex_pairs = {"EUR/USD", "GBP/USD", "USD/JPY"}
        
        new_base = new_symbol.split("/")[0] if "/" in new_symbol else new_symbol
        
        correlated_count = 0
        for pos in open_positions:
            pos_base = pos.symbol.split("/")[0] if "/" in pos.symbol else pos.symbol
            
            # Check crypto correlation
            if new_symbol in crypto_pairs and pos.symbol in crypto_pairs:
                correlated_count += 1
            # Check same base asset
            elif new_base == pos_base:
                correlated_count += 1
        
        exposure = correlated_count / max(len(open_positions), 1)
        if exposure > self._max_correlation and len(open_positions) > 0:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="correlation_exposure",
                message=f"High correlation exposure: {exposure:.0%} of positions",
                severity="warning",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="correlation_exposure",
            message=f"Correlation exposure: {exposure:.0%}",
            severity="info",
        )

    def _check_account_balance(
        self,
        request: TradeRequest,
        account_balance: float,
    ) -> SafetyConstraintResult:
        """Ensure sufficient balance for trade."""
        required = request.amount * (request.price or 0)
        if account_balance < required * 1.1:  # 10% buffer
            return SafetyConstraintResult(
                passed=False,
                constraint_name="account_balance",
                message=f"Insufficient balance: ${account_balance:.2f} < ${required * 1.1:.2f}",
                severity="critical",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="account_balance",
            message=f"Balance sufficient: ${account_balance:.2f}",
            severity="info",
        )

    def _check_position_size(
        self,
        request: TradeRequest,
        account_balance: float,
    ) -> SafetyConstraintResult:
        """Check position size limits."""
        position_value = request.amount * (request.price or 0)
        max_position = account_balance * 0.25  # Max 25% per position
        
        if position_value > max_position:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="position_size",
                message=f"Position too large: ${position_value:.2f} > ${max_position:.2f} (25% limit)",
                severity="warning",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="position_size",
            message=f"Position size: ${position_value:.2f} (max: ${max_position:.2f})",
            severity="info",
        )

    def record_trade(
        self,
        symbol: str,
        pnl_percent: float,
        side: str,
    ) -> None:
        """Record trade result for tracking."""
        self._reset_daily_if_needed()
        
        self._session.trades_today += 1
        self._session.daily_pnl += pnl_percent
        self._session.last_trade_time = datetime.utcnow()
        
        if pnl_percent < 0:
            self._session.consecutive_losses += 1
        else:
            self._session.consecutive_losses = 0
        
        self._session.position_history.append({
            "symbol": symbol,
            "side": side,
            "pnl": pnl_percent,
            "time": datetime.utcnow().isoformat(),
        })

    def record_position_open(self, position_id: str) -> None:
        """Record when a position is opened."""
        self._position_start_times[position_id] = datetime.utcnow()

    def check_position_hold_time(self, position_id: str) -> SafetyConstraintResult:
        """Check if position has exceeded max hold time."""
        if position_id not in self._position_start_times:
            return SafetyConstraintResult(
                passed=True,
                constraint_name="position_hold_time",
                message="Position time tracking not available",
                severity="info",
            )
        
        hold_time = (datetime.utcnow() - self._position_start_times[position_id]).total_seconds() / 3600
        
        if hold_time > self._max_position_hold:
            return SafetyConstraintResult(
                passed=False,
                constraint_name="position_hold_time",
                message=f"Position held {hold_time:.1f}h (max: {self._max_position_hold}h). Force exit recommended.",
                severity="warning",
            )
        return SafetyConstraintResult(
            passed=True,
            constraint_name="position_hold_time",
            message=f"Position held {hold_time:.1f}h (max: {self._max_position_hold}h)",
            severity="info",
        )

    def _reset_daily_if_needed(self) -> None:
        """Reset daily counters if new day."""
        now = datetime.utcnow()
        if now.date() != self._session.start_time.date():
            self._session = TradingSession(start_time=now)

    def get_session_stats(self) -> dict:
        """Get current session statistics."""
        return {
            "trades_today": self._session.trades_today,
            "daily_pnl": self._session.daily_pnl,
            "consecutive_losses": self._session.consecutive_losses,
            "session_start": self._session.start_time.isoformat(),
        }

    def manual_reset_daily(self, admin_token: str) -> bool:
        """Manually reset daily counters (requires admin)."""
        # Simple token check - should be more secure in production
        if not admin_token or len(admin_token) < 10:
            return False
        
        self._session = TradingSession()
        return True
