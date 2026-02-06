"""
Exit logic - stop loss, take profit, trailing stops.
"""
from __future__ import annotations

from typing import Optional
from dataclasses import dataclass

from indicators.atr import calculate_atr
from config.settings import CONFIG
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExitLevels:
    """Calculated exit levels for a position."""
    stop_loss: float
    take_profit: float
    trailing_stop: Optional[float]
    risk_reward_ratio: float


@dataclass
class ExitCheck:
    """Result of exit condition check."""
    should_exit: bool
    reason: str
    exit_price: Optional[float]
    pnl_percent: Optional[float]


def calculate_stop_loss(entry_price: float, atr: float, multiplier: float = 1.5) -> float:
    """
    Calculate stop loss price based on ATR.
    
    Args:
        entry_price: Position entry price
        atr: Average True Range value
        multiplier: ATR multiplier for stop distance
        
    Returns:
        Stop loss price
    """
    stop_distance = atr * multiplier
    return entry_price - stop_distance


def calculate_take_profit(entry_price: float, atr: float, rr_ratio: float = 2.0) -> float:
    """
    Calculate take profit price based on ATR and risk/reward.
    
    Args:
        entry_price: Position entry price
        atr: Average True Range value
        rr_ratio: Risk/Reward ratio
        
    Returns:
        Take profit price
    """
    stop_distance = atr * CONFIG.strategy.atr_stop_multiplier
    profit_distance = stop_distance * rr_ratio
    return entry_price + profit_distance


def calculate_exit_levels(
    entry_price: float,
    atr: float,
    rr_ratio: float = 2.0
) -> ExitLevels:
    """
    Calculate all exit levels for a position.
    
    Args:
        entry_price: Position entry price
        atr: ATR value
        rr_ratio: Risk/Reward ratio
        
    Returns:
        ExitLevels with stop, target, trailing
    """
    stop_loss = calculate_stop_loss(entry_price, atr)
    take_profit = calculate_take_profit(entry_price, atr, rr_ratio)
    
    # Trailing stop starts at break-even after some profit
    trailing_activation = entry_price * 1.01  # 1% profit to activate
    
    return ExitLevels(
        stop_loss=stop_loss,
        take_profit=take_profit,
        trailing_stop=None,  # Activated later
        risk_reward_ratio=rr_ratio
    )


def check_exit_conditions(
    position: dict,
    current_price: float,
    current_time: str,
    candles: list,
) -> ExitCheck:
    """
    Check if position should be exited.
    
    Args:
        position: Position dict with entry_price, stop_loss, take_profit
        current_price: Current market price
        current_time: Current timestamp
        candles: OHLCV data for ATR calculation
        
    Returns:
        ExitCheck with exit decision
    """
    entry_price = position.get("entry_price", 0)
    stop_loss = position.get("stop_loss", 0)
    take_profit = position.get("take_profit", float('inf'))
    position_side = position.get("side", "long")
    entry_time = position.get("entry_time", "")
    
    # Calculate current P&L
    if position_side == "long":
        pnl_percent = (current_price - entry_price) / entry_price * 100
    else:
        pnl_percent = (entry_price - current_price) / entry_price * 100
    
    # Check stop loss
    if position_side == "long" and current_price <= stop_loss:
        return ExitCheck(
            should_exit=True,
            reason="STOP_LOSS",
            exit_price=current_price,
            pnl_percent=pnl_percent
        )
    
    if position_side == "short" and current_price >= stop_loss:
        return ExitCheck(
            should_exit=True,
            reason="STOP_LOSS",
            exit_price=current_price,
            pnl_percent=pnl_percent
        )
    
    # Check take profit
    if position_side == "long" and current_price >= take_profit:
        return ExitCheck(
            should_exit=True,
            reason="TAKE_PROFIT",
            exit_price=current_price,
            pnl_percent=pnl_percent
        )
    
    if position_side == "short" and current_price <= take_profit:
        return ExitCheck(
            should_exit=True,
            reason="TAKE_PROFIT",
            exit_price=current_price,
            pnl_percent=pnl_percent
        )
    
    # Check time limit
    # TODO: Implement time-based exit
    
    # Check trailing stop
    highest_price = position.get("highest_price", entry_price)
    if current_price > highest_price:
        position["highest_price"] = current_price
        highest_price = current_price
    
    # Activate trailing stop after 2% profit
    if pnl_percent > 2.0:
        # Calculate trailing stop at 1.5 ATR from high
        if len(candles) >= 14:
            atr = calculate_atr(candles)[-1]
            trail_distance = atr * 1.0  # Tighter than initial stop
            trail_stop = highest_price - trail_distance
            
            if current_price <= trail_stop:
                return ExitCheck(
                    should_exit=True,
                    reason="TRAILING_STOP",
                    exit_price=current_price,
                    pnl_percent=pnl_percent
                )
    
    return ExitCheck(
        should_exit=False,
        reason="HOLD",
        exit_price=None,
        pnl_percent=pnl_percent
    )


def update_trailing_stop(
    position: dict,
    current_price: float,
    candles: list,
    activation_pct: float = 2.0,
    trail_atr_multiplier: float = 1.0
) -> Optional[float]:
    """
    Update trailing stop level if activated.
    
    Args:
        position: Position dict
        current_price: Current price
        candles: OHLCV data
        activation_pct: Profit % needed to activate trailing stop
        trail_atr_multiplier: ATR multiplier for trail distance
        
    Returns:
        New trailing stop price or None if not activated
    """
    entry_price = position.get("entry_price", 0)
    highest = position.get("highest_price", entry_price)
    
    # Update highest price
    if current_price > highest:
        position["highest_price"] = current_price
        highest = current_price
    
    # Calculate profit percentage
    profit_pct = (current_price - entry_price) / entry_price * 100
    
    # Only activate after profit threshold
    if profit_pct < activation_pct:
        return None
    
    # Calculate trailing stop
    if len(candles) >= 14:
        atr = calculate_atr(candles)[-1]
        trail_distance = atr * trail_atr_multiplier
        return highest - trail_distance
    
    # Fallback: simple percentage trailing stop
    return highest * 0.98  # 2% trailing stop
