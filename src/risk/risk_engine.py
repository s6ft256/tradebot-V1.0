"""
Risk Engine - ABSOLUTE AUTHORITY
Hard risk rules that CANNOT be overridden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List

from config.settings import CONFIG
from config.constants import (
    ABSOLUTE_MAX_RISK_PER_TRADE,
    ABSOLUTE_MAX_DAILY_LOSS,
    ABSOLUTE_MAX_DRAWDOWN
)
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskState:
    """Current risk state tracking."""
    daily_loss: float = 0.0
    daily_loss_percent: float = 0.0
    total_trades_today: int = 0
    consecutive_losses: int = 0
    max_drawdown: float = 0.0
    peak_balance: float = 0.0
    last_trade_time: Optional[datetime] = None
    emergency_stop: bool = False
    emergency_reason: Optional[str] = None


class RiskEngine:
    """
    Risk Engine with ABSOLUTE AUTHORITY.
    
    These rules override everything - AI, strategy, user settings.
    The bot CANNOT trade if risk rules are violated.
    """
    
    def __init__(self, max_risk_pct: Optional[float] = None, daily_loss_limit: Optional[float] = None):
        """
        Initialize risk engine with hard limits.
        
        Args:
            max_risk_pct: Maximum risk per trade (uses config if None)
            daily_loss_limit: Maximum daily loss (uses config if None)
        """
        self.max_risk_pct = max_risk_pct or CONFIG.risk.max_risk_per_trade_percent
        self.daily_loss_limit = daily_loss_limit or CONFIG.risk.max_daily_loss_percent
        self.max_drawdown_limit = CONFIG.risk.max_drawdown_percent
        self.max_consecutive_losses = CONFIG.risk.max_consecutive_losses
        self.max_trades_per_day = CONFIG.risk.max_trades_per_day
        self.min_time_between_trades = CONFIG.risk.min_time_between_trades_seconds
        
        # State tracking
        self.state = RiskState()
        self.trade_history: List[dict] = []
        
        # Enforce absolute limits
        self._enforce_absolute_limits()
        
        logger.info(f"RiskEngine initialized: max_risk={self.max_risk_pct}%, daily_limit={self.daily_loss_limit}%")
    
    def _enforce_absolute_limits(self) -> None:
        """Ensure no settings exceed absolute maximums."""
        if self.max_risk_pct > ABSOLUTE_MAX_RISK_PER_TRADE:
            logger.critical(f"Risk per trade capped at {ABSOLUTE_MAX_RISK_PER_TRADE}%")
            self.max_risk_pct = ABSOLUTE_MAX_RISK_PER_TRADE
        
        if self.daily_loss_limit > ABSOLUTE_MAX_DAILY_LOSS:
            logger.critical(f"Daily loss limit capped at {ABSOLUTE_MAX_DAILY_LOSS}%")
            self.daily_loss_limit = ABSOLUTE_MAX_DAILY_LOSS
        
        if self.max_drawdown_limit > ABSOLUTE_MAX_DRAWDOWN:
            logger.critical(f"Max drawdown capped at {ABSOLUTE_MAX_DRAWDOWN}%")
            self.max_drawdown_limit = ABSOLUTE_MAX_DRAWDOWN
    
    def can_open_trade(self, account_balance: float) -> bool:
        """
        Check if new trade can be opened.
        
        Args:
            account_balance: Current account balance
            
        Returns:
            True only if ALL risk checks pass
        """
        # Check emergency stop first
        if self.state.emergency_stop:
            logger.critical(f"EMERGENCY STOP ACTIVE: {self.state.emergency_reason}")
            return False
        
        # Check daily loss limit
        if self.state.daily_loss_percent >= self.daily_loss_limit:
            logger.warning(f"Daily loss limit reached: {self.state.daily_loss_percent:.2f}%")
            return False
        
        # Check max drawdown
        if self.state.max_drawdown >= self.max_drawdown_limit:
            logger.warning(f"Max drawdown reached: {self.state.max_drawdown:.2f}%")
            self._trigger_emergency("MAX_DRAWDOWN_EXCEEDED")
            return False
        
        # Check consecutive losses
        if self.state.consecutive_losses >= self.max_consecutive_losses:
            logger.warning(f"Consecutive loss limit reached: {self.state.consecutive_losses}")
            return False
        
        # Check daily trade limit
        self._reset_daily_if_needed()
        if self.state.total_trades_today >= self.max_trades_per_day:
            logger.warning(f"Daily trade limit reached: {self.state.total_trades_today}")
            return False
        
        # Check time between trades
        if not self._check_time_between_trades():
            return False
        
        # All checks passed
        return True
    
    def register_trade_open(self, position_value: float, entry_price: Optional[float]) -> None:
        """Register a new trade opening."""
        self._reset_daily_if_needed()
        self.state.total_trades_today += 1
        self.state.last_trade_time = datetime.utcnow()
        
        logger.info(f"Trade opened. Daily count: {self.state.total_trades_today}/{self.max_trades_per_day}")
    
    def register_trade_close(self, exit_price: Optional[float], amount: float, pnl_percent: Optional[float] = None) -> None:
        """
        Register a trade closing with P&L.
        
        Args:
            exit_price: Exit price
            amount: Position size
            pnl_percent: Profit/loss percentage
        """
        if pnl_percent is not None:
            self._update_daily_loss(pnl_percent)
            
            if pnl_percent < 0:
                self.state.consecutive_losses += 1
                logger.warning(f"Loss registered: {pnl_percent:.2f}% | Consecutive: {self.state.consecutive_losses}")
            else:
                if self.state.consecutive_losses > 0:
                    logger.info(f"Win after {self.state.consecutive_losses} losses: +{pnl_percent:.2f}%")
                self.state.consecutive_losses = 0
        
        # Record trade
        self.trade_history.append({
            "time": datetime.utcnow().isoformat(),
            "pnl": pnl_percent,
            "consecutive_losses": self.state.consecutive_losses
        })
    
    def _update_daily_loss(self, pnl_percent: float) -> None:
        """Update daily loss tracking."""
        if pnl_percent < 0:
            self.state.daily_loss += abs(pnl_percent)
            # Recalculate as percent of initial balance (approximated)
            # In production, use actual account balance
            logger.warning(f"Daily loss updated: {self.state.daily_loss:.2f}%")
    
    def update_balance(self, current_balance: float, initial_balance: float) -> None:
        """Update balance tracking and check drawdown."""
        # Update peak balance
        if current_balance > self.state.peak_balance:
            self.state.peak_balance = current_balance
        
        # Calculate drawdown
        if self.state.peak_balance > 0:
            drawdown = (self.state.peak_balance - current_balance) / self.state.peak_balance * 100
            self.state.max_drawdown = max(self.state.max_drawdown, drawdown)
            
            # Update daily loss percent relative to initial
            if initial_balance > 0:
                daily_pnl = (current_balance - initial_balance) / initial_balance * 100
                if daily_pnl < 0:
                    self.state.daily_loss_percent = abs(daily_pnl)
        
        # Check for emergency conditions
        if self.state.max_drawdown >= self.max_drawdown_limit:
            self._trigger_emergency("MAX_DRAWDOWN_BREACH")
        
        if self.state.daily_loss_percent >= ABSOLUTE_MAX_DAILY_LOSS:
            self._trigger_emergency("DAILY_LOSS_ABSOLUTE_LIMIT")
    
    def _check_time_between_trades(self) -> bool:
        """Check minimum time between trades."""
        if self.state.last_trade_time is None:
            return True
        
        elapsed = (datetime.utcnow() - self.state.last_trade_time).total_seconds()
        if elapsed < self.min_time_between_trades:
            logger.debug(f"Time between trades: {elapsed:.0f}s < {self.min_time_between_trades}s")
            return False
        
        return True
    
    def _reset_daily_if_needed(self) -> None:
        """Reset daily counters if new day."""
        if self.state.last_trade_time:
            now = datetime.utcnow()
            if now.date() != self.state.last_trade_time.date():
                logger.info("New trading day - resetting daily counters")
                self.state.total_trades_today = 0
                self.state.daily_loss = 0.0
                self.state.daily_loss_percent = 0.0
    
    def _trigger_emergency(self, reason: str) -> None:
        """Trigger emergency stop."""
        if not self.state.emergency_stop:
            self.state.emergency_stop = True
            self.state.emergency_reason = reason
            logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")
    
    def manual_reset(self, admin_password: str) -> bool:
        """Manual reset of emergency stop (requires password)."""
        # Simple password check - use secure method in production
        if admin_password != "EMERGENCY_RESET":
            logger.error("Invalid emergency reset password")
            return False
        
        self.state.emergency_stop = False
        self.state.emergency_reason = None
        self.state.max_drawdown = 0.0
        self.state.daily_loss = 0.0
        self.state.daily_loss_percent = 0.0
        self.state.consecutive_losses = 0
        
        logger.warning("EMERGENCY STOP MANUALLY RESET")
        return True
    
    def get_risk_report(self) -> dict:
        """Get current risk state report."""
        return {
            "daily_loss": self.state.daily_loss,
            "daily_loss_percent": self.state.daily_loss_percent,
            "max_drawdown": self.state.max_drawdown,
            "consecutive_losses": self.state.consecutive_losses,
            "trades_today": self.state.total_trades_today,
            "emergency_stop": self.state.emergency_stop,
            "can_trade": not self.state.emergency_stop and self.state.daily_loss_percent < self.daily_loss_limit,
            "limits": {
                "max_risk_per_trade": self.max_risk_pct,
                "daily_loss_limit": self.daily_loss_limit,
                "max_drawdown_limit": self.max_drawdown_limit,
                "max_trades_per_day": self.max_trades_per_day
            }
        }
