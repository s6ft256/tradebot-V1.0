"""
Entry rules - pullback entry logic.
"""
from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass

from indicators.rsi import calculate_rsi
from indicators.ema import calculate_ema
from config.settings import CONFIG
from config.constants import TREND_BULLISH
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EntrySignal:
    """Entry signal data."""
    should_enter: bool
    direction: str  # "long" or "short"
    confidence: float
    price: float
    ema_pullback: float
    rsi: float
    reason: str


def should_enter_trade(
    trend: str,
    price: float,
    ema_20: float,
    rsi: float,
    candles: List[List],
) -> bool:
    """
    Determine if we should enter a trade.
    
    Entry rules for long:
    - Trend is BULLISH
    - Price <= EMA_20 (pullback to fast EMA)
    - RSI > 50 (not oversold, showing strength)
    - RSI < 70 (not overbought)
    
    Args:
        trend: Current trend direction
        price: Current price
        ema_20: 20-period EMA
        rsi: Current RSI value
        candles: OHLCV data for additional checks
        
    Returns:
        True if entry conditions met
    """
    # Trend must be bullish for long entries
    if trend != TREND_BULLISH:
        return False
    
    # Price must be at or below EMA 20 (pullback)
    if price > ema_20 * 1.005:  # Small buffer for precision
        return False
    
    # RSI must show strength but not be overbought
    rsi_min = CONFIG.strategy.rsi_entry_min
    rsi_max = CONFIG.strategy.rsi_entry_max
    
    if rsi <= rsi_min:
        return False
    
    if rsi >= rsi_max:
        return False
    
    return True


def generate_entry_signal(
    candles: List[List],
    trend: str,
) -> EntrySignal:
    """
    Generate complete entry signal with analysis.
    
    Args:
        candles: OHLCV data
        trend: Current trend direction
        
    Returns:
        EntrySignal with all entry data
    """
    if len(candles) < 50:
        return EntrySignal(
            should_enter=False,
            direction="none",
            confidence=0.0,
            price=0,
            ema_pullback=0,
            rsi=0,
            reason="Insufficient data"
        )
    
    closes = [c[4] for c in candles]
    current_price = closes[-1]
    
    # Calculate indicators
    ema_pullback_period = CONFIG.strategy.ema_pullback
    ema_values = calculate_ema(closes, ema_pullback_period)
    ema_20 = ema_values[-1] if ema_values else current_price
    
    rsi_values = calculate_rsi(closes, CONFIG.strategy.rsi_period)
    current_rsi = rsi_values[-1] if rsi_values else 50
    
    # Check entry conditions
    entry_valid = should_enter_trade(
        trend=trend,
        price=current_price,
        ema_20=ema_20,
        rsi=current_rsi,
        candles=candles
    )
    
    if not entry_valid:
        reason = f"No entry: trend={trend}, price={current_price:.2f}, ema20={ema_20:.2f}, rsi={current_rsi:.1f}"
        return EntrySignal(
            should_enter=False,
            direction="none",
            confidence=0.0,
            price=current_price,
            ema_pullback=ema_20,
            rsi=current_rsi,
            reason=reason
        )
    
    # Calculate confidence
    confidence = _calculate_entry_confidence(
        trend, current_price, ema_20, current_rsi, candles
    )
    
    logger.info(f"Entry signal: LONG @ {current_price:.2f} | Confidence: {confidence:.2f}")
    
    return EntrySignal(
        should_enter=True,
        direction="long",
        confidence=confidence,
        price=current_price,
        ema_pullback=ema_20,
        rsi=current_rsi,
        reason="Bullish pullback entry"
    )


def _calculate_entry_confidence(
    trend: str,
    price: float,
    ema_20: float,
    rsi: float,
    candles: List[List],
) -> float:
    """Calculate entry confidence score (0.0 to 1.0)."""
    confidence = 0.5  # Base confidence
    
    # Price proximity to EMA 20 (closer = better pullback)
    ema_distance = abs(price - ema_20) / ema_20
    if ema_distance < 0.005:
        confidence += 0.2
    elif ema_distance < 0.01:
        confidence += 0.1
    
    # RSI sweet spot (55-65 is ideal)
    if 55 <= rsi <= 65:
        confidence += 0.15
    elif 50 <= rsi <= 70:
        confidence += 0.05
    
    # Cap at 1.0
    return min(confidence, 1.0)
