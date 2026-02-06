from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from paid_trading_bot.strategy.base import BaseStrategy
from paid_trading_bot.strategy.indicators import TechnicalIndicators

if TYPE_CHECKING:
    from paid_trading_bot.core.types import (
        AIGateStatus,
        Candle,
        EntrySignal,
        ExitSignal,
        Position,
        TrendBias,
    )


@dataclass
class TrendFollowingConfig:
    """Configuration for trend following strategy."""
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    min_volume_ratio: float = 1.0
    stop_loss_atr_multiplier: float = 2.0
    take_profit_atr_multiplier: float = 3.0
    max_positions_per_symbol: int = 1


class TrendFollowingStrategy(BaseStrategy):
    """
    Concrete trend following strategy using EMA crossover, RSI, and MACD.
    
    Entry Conditions:
    - Long: EMA 20 > EMA 50, RSI < 70 (not overbought), MACD bullish
    - Short: EMA 20 < EMA 50, RSI > 30 (not oversold), MACD bearish
    
    Exit Conditions:
    - Stop loss: ATR-based trailing stop
    - Take profit: Risk-reward ratio based
    - Trend reversal signal
    """

    def __init__(self, config: TrendFollowingConfig | None = None):
        self._config = config or TrendFollowingConfig()
        self._indicators = TechnicalIndicators()

    @property
    def name(self) -> str:
        return "TrendFollowingEMA"

    @property
    def description(self) -> str:
        return "EMA crossover strategy with RSI and MACD confirmation"

    def on_candles(
        self,
        ohlcv_1h: list[Candle],
        ohlcv_5m: list[Candle],
        open_positions: list[Position],
        ai_gate: AIGateStatus,
        max_positions: int,
    ) -> tuple[TrendBias, EntrySignal | None, list[ExitSignal]]:
        """Process candle data and generate trading signals."""
        if len(ohlcv_1h) < 50:
            return "neutral", None, []

        indicators = self._indicators.calculate_all(ohlcv_1h)
        current_candle = ohlcv_1h[-1]
        
        # Determine trend bias
        trend_bias = self._determine_trend_bias(indicators)
        
        # Generate entry signal
        entry_signal = None
        if ai_gate == "approved" and len(open_positions) < max_positions:
            entry_signal = self._generate_entry_signal(
                indicators, current_candle, trend_bias, open_positions
            )
        
        # Generate exit signals
        exit_signals = self._generate_exit_signals(
            indicators, current_candle, open_positions
        )
        
        return trend_bias, entry_signal, exit_signals

    def _determine_trend_bias(self, indicators) -> TrendBias:
        """Determine market trend direction."""
        if indicators.ema_20 is None or indicators.ema_50 is None:
            return "neutral"
        
        if indicators.ema_20 > indicators.ema_50:
            if indicators.macd_histogram and indicators.macd_histogram > 0:
                return "bullish"
            return "slightly_bullish"
        elif indicators.ema_20 < indicators.ema_50:
            if indicators.macd_histogram and indicators.macd_histogram < 0:
                return "bearish"
            return "slightly_bearish"
        return "neutral"

    def _generate_entry_signal(
        self,
        indicators,
        candle: Candle,
        trend_bias: TrendBias,
        open_positions: list[Position],
    ) -> EntrySignal | None:
        """Generate entry signal based on strategy rules."""
        # Check volume
        if indicators.volume_sma_20 and candle.volume < indicators.volume_sma_20 * self._config.min_volume_ratio:
            return None
        
        # Long entry conditions
        if trend_bias in ("bullish", "slightly_bullish"):
            if self._is_long_entry_valid(indicators):
                symbol_positions = [p for p in open_positions if p.symbol == candle.symbol]
                if len(symbol_positions) < self._config.max_positions_per_symbol:
                    return {
                        "symbol": candle.symbol,
                        "side": "buy",
                        "confidence": self._calculate_confidence(indicators, "buy"),
                        "reason": f"EMA bullish crossover, RSI={indicators.rsi_14:.1f}, MACD positive",
                        "suggested_stop": candle.close - (indicators.atr_14 or 0) * self._config.stop_loss_atr_multiplier,
                        "suggested_target": candle.close + (indicators.atr_14 or 0) * self._config.take_profit_atr_multiplier,
                    }
        
        # Short entry conditions
        if trend_bias in ("bearish", "slightly_bearish"):
            if self._is_short_entry_valid(indicators):
                symbol_positions = [p for p in open_positions if p.symbol == candle.symbol]
                if len(symbol_positions) < self._config.max_positions_per_symbol:
                    return {
                        "symbol": candle.symbol,
                        "side": "sell",
                        "confidence": self._calculate_confidence(indicators, "sell"),
                        "reason": f"EMA bearish crossover, RSI={indicators.rsi_14:.1f}, MACD negative",
                        "suggested_stop": candle.close + (indicators.atr_14 or 0) * self._config.stop_loss_atr_multiplier,
                        "suggested_target": candle.close - (indicators.atr_14 or 0) * self._config.take_profit_atr_multiplier,
                    }
        
        return None

    def _is_long_entry_valid(self, indicators) -> bool:
        """Check if long entry conditions are met."""
        if indicators.rsi_14 is None or indicators.rsi_14 > self._config.rsi_overbought:
            return False
        if indicators.macd_histogram is None or indicators.macd_histogram <= 0:
            return False
        return True

    def _is_short_entry_valid(self, indicators) -> bool:
        """Check if short entry conditions are met."""
        if indicators.rsi_14 is None or indicators.rsi_14 < self._config.rsi_oversold:
            return False
        if indicators.macd_histogram is None or indicators.macd_histogram >= 0:
            return False
        return True

    def _generate_exit_signals(
        self,
        indicators,
        candle: Candle,
        open_positions: list[Position],
    ) -> list[ExitSignal]:
        """Generate exit signals for open positions."""
        exits = []
        
        for position in open_positions:
            exit_signal = None
            
            # Stop loss hit
            if position.side == "buy" and candle.low <= position.stop_loss:
                exit_signal = {
                    "position_id": position.id,
                    "reason": "stop_loss",
                    "exit_price": position.stop_loss,
                }
            elif position.side == "sell" and candle.high >= position.stop_loss:
                exit_signal = {
                    "position_id": position.id,
                    "reason": "stop_loss",
                    "exit_price": position.stop_loss,
                }
            
            # Take profit hit
            elif position.side == "buy" and candle.high >= position.take_profit:
                exit_signal = {
                    "position_id": position.id,
                    "reason": "take_profit",
                    "exit_price": position.take_profit,
                }
            elif position.side == "sell" and candle.low <= position.take_profit:
                exit_signal = {
                    "position_id": position.id,
                    "reason": "take_profit",
                    "exit_price": position.take_profit,
                }
            
            # Trend reversal
            elif self._is_trend_reversal(position, indicators):
                exit_signal = {
                    "position_id": position.id,
                    "reason": "trend_reversal",
                    "exit_price": candle.close,
                }
            
            if exit_signal:
                exits.append(exit_signal)
        
        return exits

    def _is_trend_reversal(self, position: Position, indicators) -> bool:
        """Check if trend has reversed against position."""
        if position.side == "buy":
            # Bullish trend reversed
            if indicators.macd_histogram is not None and indicators.macd_histogram < 0:
                if indicators.ema_20 is not None and indicators.ema_50 is not None:
                    if indicators.ema_20 < indicators.ema_50:
                        return True
        else:
            # Bearish trend reversed
            if indicators.macd_histogram is not None and indicators.macd_histogram > 0:
                if indicators.ema_20 is not None and indicators.ema_50 is not None:
                    if indicators.ema_20 > indicators.ema_50:
                        return True
        return False

    def _calculate_confidence(self, indicators, side: str) -> float:
        """Calculate signal confidence score (0.0 - 1.0)."""
        score = 0.5
        
        if side == "buy":
            if indicators.rsi_14:
                score += (self._config.rsi_overbought - indicators.rsi_14) / 100
            if indicators.macd_histogram and indicators.macd_histogram > 0:
                score += 0.2
        else:
            if indicators.rsi_14:
                score += (indicators.rsi_14 - self._config.rsi_oversold) / 100
            if indicators.macd_histogram and indicators.macd_histogram < 0:
                score += 0.2
        
        return min(1.0, max(0.0, score))

    def validate(self) -> bool:
        """Validate strategy configuration."""
        return (
            0 < self._config.rsi_oversold < 50
            and 50 < self._config.rsi_overbought < 100
            and self._config.stop_loss_atr_multiplier > 0
            and self._config.take_profit_atr_multiplier > 0
        )
