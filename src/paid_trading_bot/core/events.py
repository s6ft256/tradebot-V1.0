from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable


class EventType(Enum):
    CANDLE_RECEIVED = auto()
    TREND_DETECTED = auto()
    ENTRY_SIGNAL = auto()
    EXIT_SIGNAL = auto()
    AI_ADVISORY = auto()
    RISK_VALIDATION = auto()
    TRADE_EXECUTED = auto()
    TRADE_REJECTED = auto()
    POSITION_OPENED = auto()
    POSITION_CLOSED = auto()
    CIRCUIT_BREAKER_TRIPPED = auto()
    CIRCUIT_BREAKER_RESET = auto()
    ERROR_OCCURRED = auto()


@dataclass(frozen=True)
class Event:
    type: EventType
    timestamp: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"


class EventBus:
    """Simple in-memory event bus for component communication."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Callable[[Event], Any]]] = {t: [] for t in EventType}

    def subscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def emit(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            try:
                handler(event)
            except Exception:
                pass  # Prevent event handler errors from breaking the chain

    def create_event(
        self,
        event_type: EventType,
        payload: dict[str, Any] | None = None,
        source: str = "unknown",
    ) -> Event:
        return Event(
            type=event_type,
            timestamp=datetime.utcnow(),
            payload=payload or {},
            source=source,
        )
