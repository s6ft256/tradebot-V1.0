from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paid_trading_bot.core.types import Candle


@dataclass
class IndicatorValues:
    """Container for technical indicator values."""
    ema_20: float | None = None
    ema_50: float | None = None
    rsi_14: float | None = None
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    atr_14: float | None = None
    volume_sma_20: float | None = None


class TechnicalIndicators:
    """Calculate technical indicators for trading decisions."""

    @staticmethod
    def calculate_ema(prices: list[float], period: int) -> float | None:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return ema

    @staticmethod
    def calculate_rsi(prices: list[float], period: int = 14) -> float | None:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return None
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        if len(gains) < period:
            return None
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(
        prices: list[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple[float | None, float | None, float | None]:
        """Calculate MACD line, signal line, and histogram."""
        if len(prices) < slow + signal:
            return None, None, None
        fast_ema = TechnicalIndicators.calculate_ema(prices, fast)
        slow_ema = TechnicalIndicators.calculate_ema(prices, slow)
        if fast_ema is None or slow_ema is None:
            return None, None, None
        macd_line = fast_ema - slow_ema
        signal_line = macd_line
        return macd_line, signal_line, macd_line - signal_line

    @staticmethod
    def calculate_atr(candles: list[Candle], period: int = 14) -> float | None:
        """Calculate Average True Range."""
        if len(candles) < period + 1:
            return None
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            true_ranges.append(max(tr1, tr2, tr3))
        if len(true_ranges) < period:
            return None
        return sum(true_ranges[-period:]) / period

    @staticmethod
    def calculate_volume_sma(volumes: list[float], period: int = 20) -> float | None:
        """Calculate Volume Simple Moving Average."""
        if len(volumes) < period:
            return None
        return sum(volumes[-period:]) / period

    @classmethod
    def calculate_all(cls, candles: list[Candle]) -> IndicatorValues:
        """Calculate all indicators for a list of candles."""
        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        macd_line, macd_signal, macd_hist = cls.calculate_macd(closes)
        return IndicatorValues(
            ema_20=cls.calculate_ema(closes, 20),
            ema_50=cls.calculate_ema(closes, 50),
            rsi_14=cls.calculate_rsi(closes, 14),
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=macd_hist,
            atr_14=cls.calculate_atr(candles, 14),
            volume_sma_20=cls.calculate_volume_sma(volumes, 20),
        )
