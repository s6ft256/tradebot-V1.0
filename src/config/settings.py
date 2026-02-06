"""
Configuration and settings for the trading bot.
Loads from environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class RiskConfig:
    """Risk management configuration - CANNOT BE OVERRIDDEN."""
    max_risk_per_trade_percent: float = 1.0
    max_daily_loss_percent: float = 3.0
    max_drawdown_percent: float = 10.0
    max_consecutive_losses: int = 5
    max_open_positions: int = 2
    max_trades_per_day: int = 6
    min_time_between_trades_seconds: int = 300
    max_position_hold_hours: int = 72
    emergency_stop_enabled: bool = True


@dataclass(frozen=True)
class StrategyConfig:
    """Strategy-specific configuration."""
    ema_fast: int = 50
    ema_slow: int = 200
    ema_pullback: int = 20
    rsi_period: int = 14
    atr_period: int = 14
    atr_stop_multiplier: float = 1.5
    rsi_entry_min: float = 50.0
    rsi_entry_max: float = 70.0


@dataclass(frozen=True)
class AIConfig:
    """AI supervisory layer configuration."""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    regime_confidence_threshold: float = 0.6
    enable_regime_filter: bool = True
    enable_risk_sentinel: bool = True
    max_ai_calls_per_hour: int = 60
    ai_prompt: str = """You are a supervisory risk intelligence for a trading bot.

Your role is to analyze market conditions and recommend trading posture.

CONSTRAINTS:
- You CANNOT predict prices
- You CANNOT bypass risk rules
- You CANNOT recommend aggressive position sizing
- You CANNOT override hard stop losses

You may only recommend one of:
1. ALLOW - Market conditions suitable for trading
2. REDUCE_RISK - Market uncertain, reduce position size
3. HALT - Market dangerous, stop trading

Analyze the provided market data and return your assessment."""


@dataclass(frozen=True)
class ExchangeConfig:
    """Exchange configuration."""
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    default_symbol: str = "BTC/USDT"
    default_timeframe: str = "1h"
    candle_limit: int = 200
    enable_rate_limit: bool = True


@dataclass(frozen=True)
class BotConfig:
    """Main bot configuration container."""
    risk: RiskConfig
    strategy: StrategyConfig
    ai: AIConfig
    exchange: ExchangeConfig
    log_level: str = "INFO"
    loop_interval_seconds: int = 60
    paper_trading: bool = True


def load_config() -> BotConfig:
    """Load configuration from environment variables."""
    
    # Risk config - these should NOT be overridable via AI
    risk_config = RiskConfig(
        max_risk_per_trade_percent=float(os.getenv("MAX_RISK_PER_TRADE", "1.0")),
        max_daily_loss_percent=float(os.getenv("MAX_DAILY_LOSS", "3.0")),
        max_drawdown_percent=float(os.getenv("MAX_DRAWDOWN", "10.0")),
        max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", "5")),
        max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "2")),
        max_trades_per_day=int(os.getenv("MAX_TRADES_PER_DAY", "6")),
        min_time_between_trades_seconds=int(os.getenv("MIN_TIME_BETWEEN_TRADES", "300")),
        max_position_hold_hours=int(os.getenv("MAX_POSITION_HOLD_HOURS", "72")),
        emergency_stop_enabled=os.getenv("EMERGENCY_STOP_ENABLED", "true").lower() == "true",
    )
    
    # Strategy config
    strategy_config = StrategyConfig(
        ema_fast=int(os.getenv("EMA_FAST", "50")),
        ema_slow=int(os.getenv("EMA_SLOW", "200")),
        ema_pullback=int(os.getenv("EMA_PULLBACK", "20")),
        rsi_period=int(os.getenv("RSI_PERIOD", "14")),
        atr_period=int(os.getenv("ATR_PERIOD", "14")),
        atr_stop_multiplier=float(os.getenv("ATR_STOP_MULTIPLIER", "1.5")),
        rsi_entry_min=float(os.getenv("RSI_ENTRY_MIN", "50.0")),
        rsi_entry_max=float(os.getenv("RSI_ENTRY_MAX", "70.0")),
    )
    
    # AI config
    ai_config = AIConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        regime_confidence_threshold=float(os.getenv("REGIME_CONFIDENCE_THRESHOLD", "0.6")),
        enable_regime_filter=os.getenv("ENABLE_REGIME_FILTER", "true").lower() == "true",
        enable_risk_sentinel=os.getenv("ENABLE_RISK_SENTINEL", "true").lower() == "true",
        max_ai_calls_per_hour=int(os.getenv("MAX_AI_CALLS_PER_HOUR", "60")),
    )
    
    # Exchange config
    exchange_config = ExchangeConfig(
        api_key=os.getenv("BINANCE_API_KEY", ""),
        api_secret=os.getenv("BINANCE_API_SECRET", ""),
        testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true",
        default_symbol=os.getenv("DEFAULT_SYMBOL", "BTC/USDT"),
        default_timeframe=os.getenv("DEFAULT_TIMEFRAME", "1h"),
        candle_limit=int(os.getenv("CANDLE_LIMIT", "200")),
        enable_rate_limit=os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true",
    )
    
    return BotConfig(
        risk=risk_config,
        strategy=strategy_config,
        ai=ai_config,
        exchange=exchange_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        loop_interval_seconds=int(os.getenv("LOOP_INTERVAL_SECONDS", "60")),
        paper_trading=os.getenv("PAPER_TRADING", "true").lower() == "true",
    )


# Global config instance
CONFIG = load_config()
