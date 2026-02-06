from __future__ import annotations

from paid_trading_bot.ai_advisory.contracts import GovernorInput, GovernorOutput, MarketRegime


class StrategyGovernorAgent:
    def run(self, data: GovernorInput) -> GovernorOutput:
        alerts: list[str] = []

        if data.regime == MarketRegime.CHOPPY:
            return GovernorOutput(
                recommendation="HALT",
                risk_multiplier=0.0,
                cooldown_minutes=0,
                reasoning="Choppy regime: no trade",
                alerts=["CHOPPY_REGIME"],
            )

        if data.daily_pnl_percent <= -2.0:
            return GovernorOutput(
                recommendation="HALT",
                risk_multiplier=0.0,
                cooldown_minutes=0,
                reasoning="Daily loss exceeded 2%",
                alerts=["DAILY_LOSS_THRESHOLD"],
            )

        if data.trades_today >= data.max_trades_per_day:
            return GovernorOutput(
                recommendation="HALT",
                risk_multiplier=0.0,
                cooldown_minutes=0,
                reasoning="Max trades per day reached",
                alerts=["MAX_TRADES_REACHED"],
            )

        if data.consecutive_losses >= 3:
            return GovernorOutput(
                recommendation="COOLDOWN",
                risk_multiplier=0.5,
                cooldown_minutes=30,
                reasoning="3 consecutive losses",
                alerts=["CONSECUTIVE_LOSSES_3"],
            )

        if data.consecutive_losses >= 2:
            alerts.append("CONSECUTIVE_LOSSES_2")
            return GovernorOutput(
                recommendation="TRADE",
                risk_multiplier=0.75,
                cooldown_minutes=0,
                reasoning="2 consecutive losses: reduce risk",
                alerts=alerts,
            )

        if data.regime == MarketRegime.HIGH_VOLATILITY:
            alerts.append("HIGH_VOLATILITY")
            return GovernorOutput(
                recommendation="TRADE",
                risk_multiplier=0.5,
                cooldown_minutes=0,
                reasoning="High volatility: reduce risk",
                alerts=alerts,
            )

        return GovernorOutput(
            recommendation="TRADE",
            risk_multiplier=1.0,
            cooldown_minutes=0,
            reasoning="Normal operation",
            alerts=alerts,
        )
