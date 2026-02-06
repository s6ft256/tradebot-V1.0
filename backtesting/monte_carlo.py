from __future__ import annotations

import random


def monte_carlo_ruin_probability(*, trade_pnls: list[float], runs: int = 1000, ruin_threshold: float = 0.5) -> float:
    if not trade_pnls:
        return 0.0

    ruined = 0
    for _ in range(runs):
        eq = 1.0
        for pnl in random.sample(trade_pnls, k=len(trade_pnls)):
            eq *= 1.0 + pnl
            if eq <= ruin_threshold:
                ruined += 1
                break

    return ruined / runs
