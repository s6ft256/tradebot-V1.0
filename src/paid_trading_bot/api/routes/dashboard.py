from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/dashboard")


@router.get("/summary")
async def summary() -> dict:
    # Placeholder for performance metrics, risk status, open positions.
    return {
        "status": "ok",
        "open_positions": 0,
        "daily_pnl_percent": 0.0,
    }
