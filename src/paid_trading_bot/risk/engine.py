from __future__ import annotations

from dataclasses import dataclass

from paid_trading_bot.core.types import AccountState, TradeRequest
from paid_trading_bot.risk.circuit_breaker import CircuitBreaker
from paid_trading_bot.risk.limits import HardRiskLimits
from paid_trading_bot.risk.validators import ValidationResult, validate_trade_request


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    details: str


class RiskEngine:
    def __init__(
        self,
        *,
        hard_limits: HardRiskLimits,
        circuit_breaker: CircuitBreaker,
    ):
        self._hard_limits = hard_limits
        self._circuit_breaker = circuit_breaker

    @property
    def hard_limits(self) -> HardRiskLimits:
        return self._hard_limits

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        return self._circuit_breaker

    def validate(self, *, request: TradeRequest, account_state: AccountState) -> RiskDecision:
        # Circuit breaker is checked elsewhere with richer SystemState; keep this deterministic.
        result: ValidationResult = validate_trade_request(
            request=request,
            account_state=account_state,
            risk_limits=self._hard_limits,
        )
        return RiskDecision(approved=result.approved, reason=result.reason, details=result.details)
