"""
Relative Strength Index (RSI) calculation.
"""
from __future__ import annotations

from typing import List


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: List of price values
        period: RSI period (default 14)
        
    Returns:
        List of RSI values (0-100)
    """
    if len(prices) < period + 1:
        return []
    
    # Calculate price changes
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [max(c, 0) for c in changes]
    losses = [abs(min(c, 0)) for c in changes]
    
    rsi_values = []
    
    # First RSI - simple average
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
    
    # Subsequent RSI values - smoothed average
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
    
    return rsi_values


def calculate_rsi_from_candles(candles: List[List], period: int = 14, price_index: int = 4) -> List[float]:
    """
    Calculate RSI from candlestick data.
    
    Args:
        candles: OHLCV data [[timestamp, open, high, low, close, volume], ...]
        period: RSI period
        price_index: Which price to use (4 = close)
        
    Returns:
        List of RSI values
    """
    prices = [c[price_index] for c in candles]
    return calculate_rsi(prices, period)


def is_oversold(rsi: float, threshold: float = 30) -> bool:
    """Check if RSI indicates oversold condition."""
    return rsi < threshold


def is_overbought(rsi: float, threshold: float = 70) -> bool:
    """Check if RSI indicates overbought condition."""
    return rsi > threshold
