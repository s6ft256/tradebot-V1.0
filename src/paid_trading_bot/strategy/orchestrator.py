from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from paid_trading_bot.core.events import Event, EventBus, EventType
from paid_trading_bot.core.types import (
    AIGateStatus,
    Candle,
    EntrySignal,
    ExitSignal,
    Position,
    TradeSide,
    TrendBias,
)
from paid_trading_bot.strategy.entry_logic import evaluate_entry
from paid_trading_bot.strategy.exit_logic import manage_exit
from paid_trading_bot.strategy.trend_follower import detect_trend


class Strategy(Protocol):
    """Abstract strategy interface."""

    def on_candles(
        self,
        ohlcv_1h: list[Candle],
        ohlcv_5m: list[Candle],
        open_positions: list[Position],
        ai_gate: AIGateStatus,
        max_positions: int,
    ) -> StrategyResult: ...


@dataclass(frozen=True)
class StrategyResult:
    trend: TrendBias
    entry_signal: EntrySignal | None
    exit_signals: list[ExitSignal]


class EMAStrategyOrchestrator:
    """Orchestrates trend detection, entry, and exit logic for EMA Trend Follower strategy."""

    def __init__(self, event_bus: EventBus | None = None):
        self._event_bus = event_bus

    def on_candles(
        self,
        ohlcv_1h: list[Candle],
        ohlcv_5m: list[Candle],
        open_positions: list[Position],
        ai_gate: AIGateStatus,
        max_positions: int,
    ) -> StrategyResult:
        # Trend detection on 1h
        trend = detect_trend(ohlcv_1h)

        if self._event_bus:
            self._event_bus.emit(
                self._event_bus.create_event(
                    EventType.TREND_DETECTED,
                    payload={"trend": trend.value},
                    source="EMAStrategyOrchestrator",
                )
            )

        # Entry signal on 5m
        entry = evaluate_entry(
            ohlcv_5m=ohlcv_5m,
            trend_bias=trend,
            ai_gate=ai_gate,
            current_positions=len(open_positions),
            max_positions=max_positions,
        )

        if entry and self._event_bus:
            self._event_bus.emit(
                self._event_bus.create_event(
                    EventType.ENTRY_SIGNAL,
                    payload={
                        "side": entry.side.value,
                        "entry_price": entry.entry_price,
                        "stop_loss": entry.stop_loss,
                    },
                    source="EMAStrategyOrchestrator",
                )
            )

        # Exit signals for open positions
        exit_signals: list[ExitSignal] = []
        current_price = ohlcv_5m[-1].close if ohlcv_5m else 0.0

        for position in open_positions:
            exit_sig = manage_exit(position=position, current_price=current_price)
            if exit_sig:
                exit_signals.append(exit_sig)
                if self._event_bus:
                    self._event_bus.emit(
                        self._event_bus.create_event(
                            EventType.EXIT_SIGNAL,
                            payload={
                                "position_id": exit_sig.position_id,
                                "exit_type": exit_sig.exit_type,
                                "exit_price": exit_sig.exit_price,
                            },
                            source="EMAStrategyOrchestrator",
                        )
                    )

        return StrategyResult(trend=trend, entry_signal=entry, exit_signals=exit_signals)
