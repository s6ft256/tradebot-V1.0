from __future__ import annotations

from fastapi import APIRouter, Depends

from paid_trading_bot.api.middleware.auth import require_api_key

router = APIRouter(prefix="/settings", dependencies=[Depends(require_api_key)])


@router.get("")
async def get_settings() -> dict:
    # Placeholder for user-configurable settings.
    return {
        "risk": {
            "max_open_positions": 2,
            "max_trades_per_day": 6,
            "max_risk_per_trade_percent": 1.0,
        }
    }
