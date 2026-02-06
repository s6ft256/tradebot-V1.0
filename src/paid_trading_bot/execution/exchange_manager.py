from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
import asyncio

import ccxt

if TYPE_CHECKING:
    from paid_trading_bot.core.types import Candle, OrderRequest, OrderResult


@dataclass
class ExchangeConfig:
    """Configuration for exchange connection."""
    exchange_id: str
    api_key: str
    api_secret: str
    passphrase: str | None = None
    sandbox: bool = True
    enable_rate_limit: bool = True
    timeout: int = 30000


@dataclass
class Balance:
    """Account balance information."""
    asset: str
    free: float
    used: float
    total: float


class ExchangeManager:
    """
    Manages connections to multiple cryptocurrency exchanges via CCXT.
    Supports Binance, Coinbase, Kraken, and others.
    """

    SUPPORTED_EXCHANGES = ["binance", "coinbase", "kraken", "kucoin", "bybit"]

    def __init__(self, config: ExchangeConfig):
        self._config = config
        self._exchange: ccxt.Exchange | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the exchange connection."""
        if self._config.exchange_id not in self.SUPPORTED_EXCHANGES:
            raise ValueError(f"Exchange {self._config.exchange_id} not supported")
        
        exchange_class = getattr(ccxt, self._config.exchange_id)
        
        config_dict = {
            "apiKey": self._config.api_key,
            "secret": self._config.api_secret,
            "enableRateLimit": self._config.enable_rate_limit,
            "timeout": self._config.timeout,
            "options": {
                "defaultType": "spot",
            },
        }
        
        if self._config.passphrase:
            config_dict["password"] = self._config.passphrase
        
        if self._config.sandbox:
            config_dict["sandbox"] = True
        
        self._exchange = exchange_class(config_dict)
        
        # Load markets
        await asyncio.to_thread(self._exchange.load_markets)
        
        self._initialized = True

    async def get_balance(self, asset: str | None = None) -> list[Balance] | Balance:
        """Get account balance."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        balance_data = await asyncio.to_thread(self._exchange.fetch_balance)
        
        balances = []
        for asset_code, data in balance_data.items():
            if asset_code in ["info", "free", "used", "total"]:
                continue
            if isinstance(data, dict) and "total" in data:
                if data["total"] > 0:
                    balances.append(Balance(
                        asset=asset_code,
                        free=data.get("free", 0),
                        used=data.get("used", 0),
                        total=data.get("total", 0),
                    ))
        
        if asset:
            for bal in balances:
                if bal.asset == asset:
                    return bal
            return Balance(asset=asset, free=0, used=0, total=0)
        
        return balances

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> list[Candle]:
        """Fetch OHLCV candlestick data."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        ohlcv = await asyncio.to_thread(
            self._exchange.fetch_ohlcv,
            symbol,
            timeframe,
            limit=limit,
        )
        
        candles = []
        for timestamp, open_p, high, low, close, volume in ohlcv:
            candles.append({
                "timestamp": timestamp,
                "open": float(open_p),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
                "symbol": symbol,
            })
        
        return candles

    async def create_order(self, request: OrderRequest) -> OrderResult:
        """Create a new order on the exchange."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        order_type_map = {
            "market": "market",
            "limit": "limit",
        }
        
        side_map = {
            "buy": "buy",
            "sell": "sell",
        }
        
        try:
            order = await asyncio.to_thread(
                self._exchange.create_order,
                request.symbol,
                order_type_map.get(request.order_type, "market"),
                side_map.get(request.side, "buy"),
                request.amount,
                request.price,
            )
            
            return {
                "order_id": order["id"],
                "symbol": order["symbol"],
                "side": request.side,
                "amount": order.get("filled", request.amount),
                "average_price": order.get("average", request.price),
                "status": order["status"],
                "fee": order.get("fee", {}).get("cost", 0),
            }
        except ccxt.InsufficientFunds as e:
            raise RuntimeError(f"Insufficient funds: {e}")
        except ccxt.InvalidOrder as e:
            raise RuntimeError(f"Invalid order: {e}")
        except ccxt.NetworkError as e:
            raise RuntimeError(f"Network error: {e}")

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        try:
            await asyncio.to_thread(self._exchange.cancel_order, order_id, symbol)
            return True
        except ccxt.OrderNotFound:
            return False

    async def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        """Get list of open orders."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        return await asyncio.to_thread(self._exchange.fetch_open_orders, symbol)

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        """Get status of a specific order."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        return await asyncio.to_thread(self._exchange.fetch_order, order_id, symbol)

    async def get_ticker(self, symbol: str) -> dict:
        """Get current ticker data for a symbol."""
        if not self._initialized or not self._exchange:
            raise RuntimeError("Exchange not initialized")
        
        return await asyncio.to_thread(self._exchange.fetch_ticker, symbol)

    async def test_connection(self) -> bool:
        """Test exchange connection and credentials."""
        try:
            await self.initialize()
            await self.get_balance()
            return True
        except Exception:
            return False

    def is_sandbox(self) -> bool:
        """Check if using sandbox mode."""
        return self._config.sandbox
