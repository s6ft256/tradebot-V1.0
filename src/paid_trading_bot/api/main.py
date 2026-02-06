from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from paid_trading_bot.api.middleware.rate_limit import InMemoryRateLimiter
from paid_trading_bot.api.routes import dashboard, health, paper, settings, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Paid Trading Bot", lifespan=lifespan)

    limiter = InMemoryRateLimiter(max_requests=120, window_seconds=60)

    app.include_router(health.router)
    app.include_router(dashboard.router, dependencies=[Depends(limiter)])
    app.include_router(settings.router)
    app.include_router(paper.router)
    app.include_router(websocket.router)

    return app


app = create_app()
