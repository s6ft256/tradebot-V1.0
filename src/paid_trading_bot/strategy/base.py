from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paid_trading_bot.core.types import (
        AIGateStatus,
        Candle,
        EntrySignal,
        ExitSignal,
        Position,
        TrendBias,
    )


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a brief description of the strategy."""
        ...

    @abstractmethod
    def on_candles(
        self,
        ohlcv_1h: list[Candle],
        ohlcv_5m: list[Candle],
        open_positions: list[Position],
        ai_gate: AIGateStatus,
        max_positions: int,
    ) -> tuple[TrendBias, EntrySignal | None, list[ExitSignal]]:
        """
        Process new candle data and return trading signals.

        Returns:
            Tuple of (trend bias, entry signal or None, list of exit signals)
        """
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Validate strategy configuration and state."""
        ...
