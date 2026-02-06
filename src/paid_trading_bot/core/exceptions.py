from __future__ import annotations


class TradingError(Exception):
    """Base exception for all trading-related errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"


class RiskError(TradingError):
    """Exception raised when risk validation fails."""

    def __init__(self, message: str, reason: str, details: str | None = None) -> None:
        super().__init__(message, code="RISK_VIOLATION")
        self.reason = reason
        self.details = details or ""


class StrategyError(TradingError):
    """Exception raised when strategy logic encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="STRATEGY_ERROR")


class ExecutionError(TradingError):
    """Exception raised when order execution fails."""

    def __init__(self, message: str, order_id: str | None = None) -> None:
        super().__init__(message, code="EXECUTION_ERROR")
        self.order_id = order_id


class CircuitBreakerError(TradingError):
    """Exception raised when circuit breaker trips or blocks operation."""

    def __init__(self, message: str, trip_reason: str | None = None) -> None:
        super().__init__(message, code="CIRCUIT_BREAKER")
        self.trip_reason = trip_reason


class ConfigurationError(TradingError):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFIG_ERROR")


class DataError(TradingError):
    """Exception raised when data operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="DATA_ERROR")
