from __future__ import annotations

from dataclasses import dataclass

from paid_trading_bot.ai_advisory.contracts import (
    GovernorInput,
    GovernorOutput,
    RegimeClassifierInput,
    RegimeClassifierOutput,
    SentinelInput,
    SentinelOutput,
)
from paid_trading_bot.ai_advisory.governor import StrategyGovernorAgent
from paid_trading_bot.ai_advisory.regime_classifier import RegimeClassifierAgent
from paid_trading_bot.ai_advisory.sentinel import RiskSentinelAgent
from paid_trading_bot.core.events import Event, EventBus, EventType


@dataclass(frozen=True)
class AIAdvisoryResult:
    regime: str
    confidence: float
    volatility_state: str
    tradeable: bool
    recommendation: str
    risk_multiplier: float
    cooldown_minutes: int
    sentinel_status: str
    anomalies: list[str]
    reasoning: str


class AIAdvisoryOrchestrator:
    """Orchestrates all 3 AI advisory agents and produces unified recommendations."""

    def __init__(self, event_bus: EventBus | None = None):
        self._regime_classifier = RegimeClassifierAgent()
        self._governor = StrategyGovernorAgent()
        self._sentinel = RiskSentinelAgent()
        self._event_bus = event_bus

    def analyze(
        self,
        *,
        regime_input: RegimeClassifierInput,
        governor_input: GovernorInput,
        sentinel_input: SentinelInput,
    ) -> AIAdvisoryResult:
        # Run all 3 agents
        regime_output: RegimeClassifierOutput = self._regime_classifier.run(regime_input)
        governor_output: GovernorOutput = self._governor.run(governor_input)
        sentinel_output: SentinelOutput = self._sentinel.run(sentinel_input)

        # Combine results
        # If sentinel is CRITICAL, override to HALT
        final_recommendation = governor_output.recommendation
        final_risk_multiplier = governor_output.risk_multiplier
        final_cooldown = governor_output.cooldown_minutes

        if sentinel_output.status == "CRITICAL":
            final_recommendation = "HALT"
            final_risk_multiplier = 0.0
            final_cooldown = 0

        result = AIAdvisoryResult(
            regime=regime_output.regime,
            confidence=regime_output.confidence,
            volatility_state=regime_output.volatility_state,
            tradeable=regime_output.tradeable and final_recommendation == "TRADE",
            recommendation=final_recommendation,
            risk_multiplier=final_risk_multiplier,
            cooldown_minutes=final_cooldown,
            sentinel_status=sentinel_output.status,
            anomalies=sentinel_output.anomalies_detected,
            reasoning=f"Regime: {regime_output.reasoning}; Governor: {governor_output.reasoning}; Sentinel: {sentinel_output.explanation}",
        )

        if self._event_bus:
            event = self._event_bus.create_event(
                EventType.AI_ADVISORY,
                payload={
                    "regime": result.regime,
                    "recommendation": result.recommendation,
                    "risk_multiplier": result.risk_multiplier,
                    "sentinel_status": result.sentinel_status,
                },
                source="AIAdvisoryOrchestrator",
            )
            self._event_bus.emit(event)

        return result
