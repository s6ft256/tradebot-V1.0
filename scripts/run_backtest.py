from __future__ import annotations

import argparse

from paid_trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from paid_trading_bot.risk.engine import RiskEngine
from paid_trading_bot.risk.limits import HardRiskLimits

from backtesting.engine import BacktestConfig, BacktestEngine
from backtesting.metrics import compute_metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    args = parser.parse_args()

    risk = RiskEngine(hard_limits=HardRiskLimits(), circuit_breaker=CircuitBreaker(CircuitBreakerConfig()))

    # Backtesting skeleton currently expects candle inputs; pass empty lists.
    engine = BacktestEngine(risk_engine=risk)
    res = engine.run(config=BacktestConfig(symbol=args.symbol), candles_1h=[], candles_5m=[])
    metrics = compute_metrics(trade_pnls=res.trade_pnls, equity_curve=res.equity_curve)

    print({"symbol": args.symbol, **metrics.__dict__})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
