from __future__ import annotations

from fastapi import APIRouter

from paid_trading_bot.api.schemas.api_models import PaperOrderRequest, PaperOrderResponse
from paid_trading_bot.execution.engine import ExecutionEngine, OrderRequest
from paid_trading_bot.execution.order_manager import OrderManager
from paid_trading_bot.execution.paper_trading import PaperTradingBroker

router = APIRouter(prefix="/paper")

_paper_broker = PaperTradingBroker()
_exec = ExecutionEngine(order_manager=OrderManager(), paper_broker=_paper_broker)


@router.post("/order", response_model=PaperOrderResponse)
async def paper_order(req: PaperOrderRequest) -> PaperOrderResponse:
    exec_res = await _exec.execute(
        req=OrderRequest(
            symbol=req.symbol,
            order_type=req.order_type,
            side=req.side,
            amount=req.amount,
            price=req.price,
        ),
        current_price=req.current_price,
    )
    return PaperOrderResponse(
        order_id=exec_res.order_id,
        symbol=exec_res.symbol,
        side=exec_res.side,
        amount=exec_res.amount,
        average_price=exec_res.average_price,
        status=exec_res.status,
    )
