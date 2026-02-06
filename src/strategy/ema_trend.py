"""
EMA trend detection - 50/200 golden cross strategy.
"""
from __future__ import annotations

from typing import List
from dataclasses import dataclass

from indicators.ema import calculate_ema
from config.constants import TREND_BULLISH, TREND_BEARISH, TREND_NEUTRAL
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrendState:
    """Current trend state."""
    direction: str
    ema_fast: float
    ema_slow: float
    strength: float  # 0.0 to 1.0
    candles_count: int


def get_trend_bias(ema_50: float, ema_200: float) -> str:
    """
    Determine trend bias from EMA cross.
    
    Args:
        ema_50: Fast EMA value
        ema_200: Slow EMA value
        
    Returns:
        TREND_BULLISH, TREND_BEARISH, or TREND_NEUTRAL
    """
    if ema_50 > ema_200:
        return TREND_BULLISH
    elif ema_50 < ema_200:
        return TREND_BEARISH
    return TREND_NEUTRAL


def calculate_trend_strength(ema_50: float, ema_200: float, price: float) -> float:
    """
    Calculate trend strength (0.0 to 1.0).
    
    Based on EMA separation and price alignment.
    """
    if ema_200 == 0:
        return 0.0
    
    # EMA separation ratio
    ema_diff = abs(ema_50 - ema_200) / ema_200
    
    # Price alignment with trend
    trend = get_trend_bias(ema_50, ema_200)
    
    if trend == TREND_BULLISH:
        aligned = price > ema_50
    elif trend == TREND_BEARISH:
        aligned = price < ema_50
    else:
        aligned = False
    
    # Strength calculation
    base_strength = min(ema_diff * 100, 0.7)  # Max 0.7 from EMA diff
    alignment_bonus = 0.3 if aligned else 0.0
    
    return min(base_strength + alignment_bonus, 1.0)


def analyze_trend(candles: List[List], ema_fast: int = 50, ema_slow: int = 200) -> TrendState:
    """
    Analyze market trend from candle data.
    
    Args:
        candles: OHLCV data [[timestamp, open, high, low, close, volume], ...]
        ema_fast: Fast EMA period
        ema_slow: Slow EMA period
        
    Returns:
        TrendState with direction and strength
    """
    if len(candles) < ema_slow + 10:
        logger.warning(f"Insufficient candles for trend analysis: {len(candles)}")
        return TrendState(TREND_NEUTRAL, 0, 0, 0, len(candles))
    
    # Extract close prices
    closes = [c[4] for c in candles]
    
    # Calculate EMAs
    ema_fast_values = calculate_ema(closes, ema_fast)
    ema_slow_values = calculate_ema(closes, ema_slow)
    
    if len(ema_fast_values) == 0 or len(ema_slow_values) == 0:
        return TrendState(TREND_NEUTRAL, 0, 0, 0, len(candles))
    
    current_fast = ema_fast_values[-1]
    current_slow = ema_slow_values[-1]
    current_price = closes[-1]
    
    # Determine trend
    trend_direction = get_trend_bias(current_fast, current_slow)
    trend_strength = calculate_trend_strength(current_fast, current_slow, current_price)
    
    logger.info(f"Trend: {trend_direction} | Fast: {current_fast:.2f} | Slow: {current_slow:.2f} | Strength: {trend_strength:.2f}")
    
    return TrendState(
        direction=trend_direction,
        ema_fast=current_fast,
        ema_slow=current_slow,
        strength=trend_strength,
        candles_count=len(candles)
    )
