"""
General helper utilities.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from decimal import Decimal, ROUND_DOWN


def round_down(value: float, decimals: int = 8) -> float:
    """Round down to specified decimal places."""
    d = Decimal(str(value))
    return float(d.quantize(Decimal(10) ** -decimals, rounding=ROUND_DOWN))


def format_price(price: float, precision: int = 2) -> str:
    """Format price for display."""
    return f"${price:,.{precision}f}"


def format_percent(value: float, precision: int = 2) -> str:
    """Format percentage for display."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{precision}f}%"


def calculate_position_size(balance: float, risk_percent: float, entry_price: float, stop_price: float) -> float:
    """
    Calculate position size based on risk parameters.
    
    Args:
        balance: Account balance
        risk_percent: Risk percentage per trade
        entry_price: Entry price
        stop_price: Stop loss price
        
    Returns:
        Position size in base currency
    """
    if stop_price >= entry_price:
        return 0.0
    
    risk_amount = balance * (risk_percent / 100)
    price_risk = entry_price - stop_price
    
    if price_risk <= 0:
        return 0.0
    
    position_size = risk_amount / price_risk
    return round_down(position_size, 6)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value."""
    if denominator == 0:
        return default
    return numerator / denominator


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, with override taking precedence."""
    result = base.copy()
    result.update(override)
    return result


def truncate_list(items: List[Any], max_size: int) -> List[Any]:
    """Truncate list to maximum size, keeping most recent items."""
    if len(items) <= max_size:
        return items
    return items[-max_size:]


def is_valid_symbol(symbol: str) -> bool:
    """Check if symbol format is valid."""
    if not symbol or "/" not in symbol:
        return False
    parts = symbol.split("/")
    return len(parts) == 2 and all(len(p) > 0 for p in parts)
