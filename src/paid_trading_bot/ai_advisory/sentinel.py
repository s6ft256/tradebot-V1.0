from __future__ import annotations

from paid_trading_bot.ai_advisory.contracts import SentinelInput, SentinelOutput


class RiskSentinelAgent:
    def run(self, data: SentinelInput) -> SentinelOutput:
        anomalies: list[str] = []

        status = "HEALTHY"
        action = "NONE"

        if data.average_slippage_bps > 50:
            anomalies.append("HIGH_SLIPPAGE")
            status = "WARNING"
            action = "REDUCE_SIZE"

        if data.api_error_count_1h > 5:
            anomalies.append("API_ERRORS")
            status = "CRITICAL"
            action = "PAUSE"

        bal_disc_pct = 0.0
        if data.expected_balance > 0:
            bal_disc_pct = abs(data.account_balance - data.expected_balance) / data.expected_balance * 100.0

        if bal_disc_pct > 1.0:
            anomalies.append("BALANCE_MISMATCH")
            status = "CRITICAL"
            action = "EMERGENCY_HALT"

        if str(data.exchange_status).upper() != "NORMAL":
            anomalies.append("EXCHANGE_STATUS")
            status = "CRITICAL"
            action = "PAUSE"

        return SentinelOutput(
            status=status,
            anomalies_detected=anomalies,
            action_required=action,
            explanation="; ".join(anomalies) if anomalies else "No anomalies",
        )
