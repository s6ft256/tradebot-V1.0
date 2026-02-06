from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from paid_trading_bot.core.events import EventBus
from paid_trading_bot.core.types import AccountState, Candle, Position
from paid_trading_bot.data.ingestion import DataIngestion
from paid_trading_bot.data.ohlcv_buffer import OHLCVBuffer, OHLCVBufferConfig
from paid_trading_bot.execution.engine import ExecutionEngine
from paid_trading_bot.risk.engine import RiskEngine
from paid_trading_bot.strategy.orchestrator import EMAStrategyOrchestrator, StrategyResult


@dataclass
class TradingContext:
    account_state: AccountState
    open_positions: list[Position]
    candles_1h: list[Candle]
    candles_5m: list[Candle]


class TradingOrchestrator:
    """Main 5-minute trading loop orchestrator."""

    def __init__(
        self,
        *,
        data_ingestion: DataIngestion,
        strategy: EMAStrategyOrchestrator,
        risk_engine: RiskEngine,
        execution: ExecutionEngine,
        event_bus: EventBus | None = None,
    ):
        self._ingestion = data_ingestion
        self._strategy = strategy
        self._risk = risk_engine
        self._execution = execution
        self._event_bus = event_bus

        self._buffer_1h = OHLCVBuffer(OHLCVBufferConfig(maxlen=200))
        self._buffer_5m = OHLCVBuffer(OHLCVBufferConfig(maxlen=100))
        self._running = False

    async def fetch_data(self, symbol: str) -> None:
        candles_1h = await self._ingestion.fetch_candles(symbol=symbol, timeframe="1h", limit=200)
        candles_5m = await self._ingestion.fetch_candles(symbol=symbol, timeframe="5m", limit=100)
        self._buffer_1h.extend(candles_1h)
        self._buffer_5m.extend(candles_5m)

    def evaluate_strategy(self, context: TradingContext) -> StrategyResult:
        from paid_trading_bot.core.types import AIGateStatus
        return self._strategy.on_candles(
            ohlcv_1h=context.candles_1h,
            ohlcv_5m=context.candles_5m,
            open_positions=context.open_positions,
            ai_gate=AIGateStatus.OPEN,
            max_positions=self._risk.hard_limits.max_open_positions,
        )

    async def run_cycle(self, symbol: str, account_state: AccountState) -> None:
        await self.fetch_data(symbol)
        context = TradingContext(
            account_state=account_state,
            open_positions=[],
            candles_1h=self._buffer_1h.snapshot(),
            candles_5m=self._buffer_5m.snapshot(),
        )
        result = self.evaluate_strategy(context)
        # Risk validation and execution would go here
