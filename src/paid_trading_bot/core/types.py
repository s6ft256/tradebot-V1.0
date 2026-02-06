from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class TrendBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class TradeSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class AIGateStatus(str, Enum):
    OPEN = "OPEN"
    COOLDOWN = "COOLDOWN"
    HALT = "HALT"


@dataclass(frozen=True)
class EntrySignal:
    side: TradeSide
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    atr: float


@dataclass(frozen=True)
class ExitSignal:
    position_id: str
    exit_type: str
    exit_price: float
    size_percent: float


@dataclass
class Position:
    id: str
    symbol: str
    side: TradeSide
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    entry_atr: float
    size: float
    opened_at: datetime

    tp1_hit: bool = False
    highest_price: float | None = None
    lowest_price: float | None = None


@dataclass(frozen=True)
class TradeRequest:
    symbol: str
    side: TradeSide
    entry_price: float
    stop_loss: float
    position_size: float
    timestamp: datetime


@dataclass
class AccountState:
    balance: float
    daily_pnl_percent: float
    current_drawdown_percent: float
    consecutive_losses: int
    open_positions: int
    trades_today: int
