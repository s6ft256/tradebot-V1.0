from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from paid_trading_bot.execution.ccxt_adapter import CCXTAdapter
from paid_trading_bot.execution.order_manager import OrderManager
from paid_trading_bot.execution.paper_trading import PaperTradingBroker, PaperFill


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    order_type: str  # market|limit
    side: str  # buy|sell
    amount: float
    price: float | None = None


@dataclass(frozen=True)
class OrderExecution:
    order_id: str
    symbol: str
    side: str
    amount: float
    average_price: float
    status: str
    timestamp: datetime


class ExecutionEngine:
    def __init__(
        self,
        *,
        order_manager: OrderManager,
        ccxt_adapter: CCXTAdapter | None = None,
        paper_broker: PaperTradingBroker | None = None,
    ):
        self._om = order_manager
        self._ccxt = ccxt_adapter
        self._paper = paper_broker

        if (self._ccxt is None) == (self._paper is None):
            raise ValueError("provide exactly one of ccxt_adapter or paper_broker")

    async def execute(self, *, req: OrderRequest, current_price: float | None = None) -> OrderExecution:
        if self._paper is not None:
            fill: PaperFill = await self._om.with_retries(
                self._paper.create_order,
                symbol=req.symbol,
                order_type=req.order_type,
                side=req.side,
                amount=req.amount,
                price=req.price,
                current_price=current_price,
            )
            return OrderExecution(
                order_id=fill.order_id,
                symbol=fill.symbol,
                side=fill.side,
                amount=fill.amount,
                average_price=fill.price,
                status="filled",
                timestamp=fill.timestamp,
            )

        assert self._ccxt is not None
        order = await self._om.with_retries(
            self._ccxt.create_order,
            symbol=req.symbol,
            order_type=req.order_type,
            side=req.side,
            amount=req.amount,
            price=req.price,
        )

        avg_price = order.get("average") or order.get("price")
        return OrderExecution(
            order_id=str(order.get("id")),
            symbol=req.symbol,
            side=req.side,
            amount=req.amount,
            average_price=float(avg_price) if avg_price is not None else 0.0,
            status=str(order.get("status") or "unknown"),
            timestamp=datetime.utcnow(),
        )
