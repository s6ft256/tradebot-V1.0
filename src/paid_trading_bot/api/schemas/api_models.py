from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")


class PaperOrderRequest(BaseModel):
    symbol: str
    order_type: str = Field(description="market|limit")
    side: str = Field(description="buy|sell")
    amount: float
    price: float | None = None
    current_price: float | None = None


class PaperOrderResponse(BaseModel):
    order_id: str
    symbol: str
    side: str
    amount: float
    average_price: float
    status: str
