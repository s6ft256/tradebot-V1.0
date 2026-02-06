from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CircuitBreakerConfig:
    emergency_drawdown_percent: float = 10.0
    max_api_failures: int = 5
    balance_tolerance_percent: float = 1.0


@dataclass(frozen=True)
class SystemState:
    drawdown_percent: float
    sentinel_status: str
    sentinel_reason: str | None
    api_consecutive_failures: int
    balance_discrepancy_percent: float


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self._config = config
        self.is_tripped: bool = False
        self.trip_reason: str | None = None
        self.trip_timestamp: datetime | None = None

    def check_and_trip(self, state: SystemState) -> bool:
        if self.is_tripped:
            return True

        trip_conditions: list[tuple[bool, str]] = [
            (
                state.drawdown_percent >= self._config.emergency_drawdown_percent,
                f"EMERGENCY_DRAWDOWN: {state.drawdown_percent}%",
            ),
            (
                state.sentinel_status.upper() == "CRITICAL",
                f"SENTINEL_CRITICAL: {state.sentinel_reason}",
            ),
            (
                state.api_consecutive_failures >= self._config.max_api_failures,
                f"API_FAILURES: {state.api_consecutive_failures}",
            ),
            (
                state.balance_discrepancy_percent > self._config.balance_tolerance_percent,
                f"BALANCE_MISMATCH: {state.balance_discrepancy_percent}%",
            ),
        ]

        for condition, reason in trip_conditions:
            if condition:
                self._trip(reason)
                return True

        return False

    def _trip(self, reason: str) -> None:
        self.is_tripped = True
        self.trip_reason = reason
        self.trip_timestamp = datetime.utcnow()

    def manual_reset(self, *, admin_token: str) -> bool:
        if not self._verify_admin_token(admin_token):
            return False

        self.is_tripped = False
        self.trip_reason = None
        self.trip_timestamp = None
        return True

    def _verify_admin_token(self, admin_token: str) -> bool:
        return bool(admin_token)
