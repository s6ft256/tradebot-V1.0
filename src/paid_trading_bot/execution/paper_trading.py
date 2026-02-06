from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PaperFill:
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float
    timestamp: datetime


class PaperTradingBroker:
    def __init__(self):
        self._order_seq = 0
        self.fills: list[PaperFill] = []

    def _next_order_id(self) -> str:
        self._order_seq += 1
        return f"paper-{self._order_seq}"

    async def create_order(
        self,
        *,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
        current_price: float | None = None,
    ) -> PaperFill:
        if order_type not in {"market", "limit"}:
            raise ValueError("paper broker supports market|limit")

        fill_price = price
        if order_type == "market":
            if current_price is None:
                raise ValueError("current_price required for market paper fills")
            fill_price = current_price

        if fill_price is None:
            raise ValueError("price required")

        fill = PaperFill(
            order_id=self._next_order_id(),
            symbol=symbol,
            side=side,
            amount=amount,
            price=float(fill_price),
            timestamp=datetime.utcnow(),
        )
        self.fills.append(fill)
        return fill
