from __future__ import annotations

import pytest

from paid_trading_bot.core.events import EventBus
from paid_trading_bot.core.types import Candle, TradeSide
from paid_trading_bot.risk.circuit_breaker import CircuitBreaker
from paid_trading_bot.risk.engine import RiskEngine
from paid_trading_bot.risk.limits import HardRiskLimits


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def sample_candles() -> list[Candle]:
    return [
        Candle(open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0),
        Candle(open=100.5, high=102.0, low=100.0, close=101.5, volume=1200.0),
        Candle(open=101.5, high=103.0, low=101.0, close=102.5, volume=1500.0),
        Candle(open=102.5, high=104.0, low=102.0, close=103.5, volume=2000.0),
        Candle(open=103.5, high=105.0, low=103.0, close=104.5, volume=1800.0),
    ]


@pytest.fixture
def hard_limits() -> HardRiskLimits:
    return HardRiskLimits(
        max_risk_per_trade_percent=1.0,
        min_risk_per_trade_percent=0.5,
        daily_loss_cap_percent=3.0,
        max_drawdown_percent=10.0,
        max_consecutive_losses=5,
        max_open_positions=2,
        max_trades_per_day=6,
        max_slippage_percent=0.5,
        api_key_withdrawal_check=True,
    )


@pytest.fixture
def circuit_breaker(hard_limits: HardRiskLimits) -> CircuitBreaker:
    return CircuitBreaker(
        max_daily_loss_pct=hard_limits.daily_loss_cap_percent,
        daily_reset_time=None,
    )


@pytest.fixture
def risk_engine(hard_limits: HardRiskLimits) -> RiskEngine:
    return RiskEngine(hard_limits=hard_limits)
