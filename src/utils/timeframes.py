"""
Timeframe utilities for trading.
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta


def timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes."""
    mapping = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "3d": 4320,
        "1w": 10080,
    }
    return mapping.get(timeframe, 60)


def get_candle_timestamp(timestamp_ms: int) -> datetime:
    """Convert millisecond timestamp to datetime."""
    return datetime.utcfromtimestamp(timestamp_ms / 1000)


def format_timeframe(timeframe: str) -> str:
    """Format timeframe for display."""
    return timeframe.upper()


def get_next_candle_time(timeframe: str, now: Optional[datetime] = None) -> datetime:
    """Get the timestamp of the next candle close."""
    if now is None:
        now = datetime.utcnow()
    
    minutes = timeframe_to_minutes(timeframe)
    minutes_since_midnight = now.hour * 60 + now.minute
    minutes_until_next = minutes - (minutes_since_midnight % minutes)
    
    if minutes_until_next == minutes:
        minutes_until_next = 0
    
    next_time = now + timedelta(minutes=minutes_until_next)
    return next_time.replace(second=0, microsecond=0)


def should_update(timeframe: str, last_update: Optional[datetime]) -> bool:
    """Check if enough time has passed to update for given timeframe."""
    if last_update is None:
        return True
    
    minutes = timeframe_to_minutes(timeframe)
    elapsed = (datetime.utcnow() - last_update).total_seconds() / 60
    
    return elapsed >= minutes
