from __future__ import annotations

from fastapi import APIRouter

from paid_trading_bot.api.schemas.api_models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
