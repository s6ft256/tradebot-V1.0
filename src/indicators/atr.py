"""
Average True Range (ATR) calculation for volatility measurement.
"""
from __future__ import annotations

from typing import List


def calculate_true_range(candles: List[List]) -> List[float]:
    """
    Calculate True Range from candlestick data.
    
    TR = max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )
    
    Args:
        candles: OHLCV data [[timestamp, open, high, low, close, volume], ...]
        
    Returns:
        List of True Range values
    """
    tr_values = []
    
    for i in range(len(candles)):
        if i == 0:
            # First candle - just use high-low
            tr = candles[i][2] - candles[i][3]  # high - low
        else:
            high = candles[i][2]
            low = candles[i][3]
            prev_close = candles[i-1][4]
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            tr = max(tr1, tr2, tr3)
        
        tr_values.append(tr)
    
    return tr_values


def calculate_atr(candles: List[List], period: int = 14) -> List[float]:
    """
    Calculate Average True Range.
    
    Args:
        candles: OHLCV data
        period: ATR period (default 14)
        
    Returns:
        List of ATR values
    """
    if len(candles) < period:
        return []
    
    tr_values = calculate_true_range(candles)
    atr_values = []
    
    # First ATR - simple average
    atr = sum(tr_values[:period]) / period
    atr_values.append(atr)
    
    # Subsequent ATR - smoothed
    for i in range(period, len(tr_values)):
        atr = (atr * (period - 1) + tr_values[i]) / period
        atr_values.append(atr)
    
    return atr_values


def calculate_volatility_percent(candles: List[List], period: int = 14) -> float:
    """
    Calculate current volatility as percentage of price.
    
    Returns:
        ATR as percentage of current price
    """
    if len(candles) < period:
        return 0.0
    
    atr_values = calculate_atr(candles, period)
    if not atr_values:
        return 0.0
    
    current_price = candles[-1][4]  # close price
    if current_price == 0:
        return 0.0
    
    return (atr_values[-1] / current_price) * 100
