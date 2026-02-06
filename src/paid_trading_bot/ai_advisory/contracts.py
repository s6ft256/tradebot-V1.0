from __future__ import annotations

from dataclasses import dataclass

from paid_trading_bot.core.types import Candle


class MarketRegime(str):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    CHOPPY = "CHOPPY"


@dataclass(frozen=True)
class RegimeClassifierInput:
    ohlcv_1h: list[Candle]
    ohlcv_5m: list[Candle]
    current_atr_percentile: float
    ema50_ema200_spread: float
    recent_price_range: float


@dataclass(frozen=True)
class RegimeClassifierOutput:
    regime: str
    confidence: float
    volatility_state: str
    tradeable: bool
    reasoning: str


@dataclass(frozen=True)
class GovernorInput:
    regime: str
    regime_confidence: float
    daily_pnl_percent: float
    weekly_pnl_percent: float
    consecutive_losses: int
    consecutive_wins: int
    current_drawdown_percent: float
    trades_today: int
    max_trades_per_day: int
    last_trade_outcome: str
    time_since_last_trade_mins: int


@dataclass(frozen=True)
class GovernorOutput:
    recommendation: str
    risk_multiplier: float
    cooldown_minutes: int
    reasoning: str
    alerts: list[str]


@dataclass(frozen=True)
class SentinelInput:
    last_10_orders: list[object]
    average_slippage_bps: float
    api_error_count_1h: int
    latency_p95_ms: float
    current_spread_bps: float
    account_balance: float
    expected_balance: float
    exchange_status: str


@dataclass(frozen=True)
class SentinelOutput:
    status: str
    anomalies_detected: list[str]
    action_required: str
    explanation: str
