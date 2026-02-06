from __future__ import annotations

from paid_trading_bot.ai_advisory.contracts import (
    MarketRegime,
    RegimeClassifierInput,
    RegimeClassifierOutput,
)


class RegimeClassifierAgent:
    def run(self, data: RegimeClassifierInput) -> RegimeClassifierOutput:
        # Baseline deterministic rules (no external AI): if spread is large => trending.
        spread = data.ema50_ema200_spread
        atr_pct = data.current_atr_percentile

        if atr_pct >= 90:
            return RegimeClassifierOutput(
                regime=MarketRegime.HIGH_VOLATILITY,
                confidence=0.7,
                volatility_state="EXTREME",
                tradeable=True,
                reasoning="ATR percentile >= 90: high volatility, reduce size",
            )

        if abs(spread) < 1.0:
            return RegimeClassifierOutput(
                regime=MarketRegime.RANGING,
                confidence=0.6,
                volatility_state="NORMAL",
                tradeable=True,
                reasoning="EMA spread < 1%: ranging",
            )

        if spread >= 1.0:
            return RegimeClassifierOutput(
                regime=MarketRegime.TRENDING_UP,
                confidence=0.7,
                volatility_state="NORMAL",
                tradeable=True,
                reasoning="EMA50 above EMA200 by >= 1%",
            )

        return RegimeClassifierOutput(
            regime=MarketRegime.TRENDING_DOWN,
            confidence=0.7,
            volatility_state="NORMAL",
            tradeable=True,
            reasoning="EMA50 below EMA200 by <= -1%",
        )
