"""
Exponential Moving Average (EMA) calculation.
"""
from __future__ import annotations

from typing import List


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: List of price values
        period: EMA period
        
    Returns:
        List of EMA values (same length as input, first values are None until period)
    """
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    
    # Start with SMA for first value
    ema_values = []
    sma = sum(prices[:period]) / period
    ema_values.append(sma)
    
    # Calculate EMA for remaining values
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(ema)
    
    return ema_values


def calculate_ema_series(candles: List[List], period: int, price_index: int = 4) -> List[float]:
    """
    Calculate EMA from candlestick data.
    
    Args:
        candles: OHLCV data [[timestamp, open, high, low, close, volume], ...]
        period: EMA period
        price_index: Which price to use (4 = close)
        
    Returns:
        List of EMA values
    """
    prices = [c[price_index] for c in candles]
    return calculate_ema(prices, period)
