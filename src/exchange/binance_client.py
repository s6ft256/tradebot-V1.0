"""
Binance API client wrapper using CCXT.
Handles all exchange communication.
"""
from __future__ import annotations

import ccxt
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from config.settings import CONFIG
from config.constants import (
    SYMBOL_BTC_USDT, SIDE_BUY, SIDE_SELL,
    ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT
)
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OrderResult:
    """Result of an order execution."""
    success: bool
    order_id: Optional[str]
    symbol: str
    side: str
    amount: float
    price: Optional[float]
    status: str
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class Balance:
    """Account balance information."""
    asset: str
    free: float
    used: float
    total: float


class BinanceClient:
    """
    Binance exchange client wrapper.
    
    Uses CCXT for unified API access.
    Trade-only keys - no withdrawal permissions.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: Optional[bool] = None):
        """
        Initialize Binance client.
        
        Args:
            api_key: API key (overrides config if provided)
            api_secret: API secret (overrides config if provided)
            testnet: Use testnet (overrides config if provided)
        """
        self.api_key = api_key or CONFIG.exchange.api_key
        self.api_secret = api_secret or CONFIG.exchange.api_secret
        self.testnet = testnet if testnet is not None else CONFIG.exchange.testnet
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API credentials not configured")
        
        # Initialize CCXT client
        config = {
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": CONFIG.exchange.enable_rate_limit,
            "options": {
                "defaultType": "spot",
            }
        }
        
        if self.testnet:
            config["sandbox"] = True
            config["options"]["test"] = True
        
        self.client = ccxt.binance(config)
        
        logger.info(f"Binance client initialized (testnet={self.testnet})")
    
    def fetch_ohlcv(self, symbol: str = SYMBOL_BTC_USDT, timeframe: str = "1h", limit: int = 200) -> List[List]:
        """
        Fetch OHLCV (candlestick) data.
        
        Returns list of [timestamp, open, high, low, close, volume]
        """
        try:
            candles = self.client.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.debug(f"Fetched {len(candles)} candles for {symbol} {timeframe}")
            return candles
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV: {e}")
            raise
    
    def get_balance(self, asset: Optional[str] = None) -> Dict[str, Balance] | Balance:
        """
        Fetch account balance.
        
        Args:
            asset: Specific asset to query, or None for all
            
        Returns:
            Balance object or dict of all balances
        """
        try:
            response = self.client.fetch_balance()
            
            balances = {}
            for currency, data in response.items():
                if isinstance(data, dict) and "free" in data:
                    balance = Balance(
                        asset=currency,
                        free=data.get("free", 0),
                        used=data.get("used", 0),
                        total=data.get("total", 0)
                    )
                    if balance.total > 0:
                        balances[currency] = balance
            
            if asset:
                return balances.get(asset, Balance(asset=asset, free=0, used=0, total=0))
            
            logger.info(f"Fetched balances for {len(balances)} assets")
            return balances
            
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> OrderResult:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            side: "buy" or "sell"
            amount: Order size in base currency
            
        Returns:
            OrderResult with execution details
        """
        try:
            logger.info(f"Placing market {side} order: {amount} {symbol}")
            
            order = self.client.create_market_order(symbol, side, amount)
            
            result = OrderResult(
                success=True,
                order_id=order.get("id"),
                symbol=symbol,
                side=side,
                amount=amount,
                price=order.get("average"),
                status=order.get("status", "unknown"),
                raw_response=order
            )
            
            logger.info(f"Order executed: {result.order_id} at {result.price}")
            return result
            
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                symbol=symbol,
                side=side,
                amount=amount,
                price=None,
                status="failed",
                error=str(e)
            )
    
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> OrderResult:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            amount: Order size
            price: Limit price
        """
        try:
            logger.info(f"Placing limit {side} order: {amount} {symbol} @ {price}")
            
            order = self.client.create_limit_order(symbol, side, amount, price)
            
            return OrderResult(
                success=True,
                order_id=order.get("id"),
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                status=order.get("status", "open"),
                raw_response=order
            )
            
        except Exception as e:
            logger.error(f"Limit order failed: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                status="failed",
                error=str(e)
            )
    
    def place_stop_loss_order(self, symbol: str, side: str, amount: float, stop_price: float) -> OrderResult:
        """
        Place a stop-loss order.
        
        Note: Binance specific implementation.
        Uses stop-loss-limit for spot markets.
        """
        try:
            logger.info(f"Placing stop-loss: {side} {amount} {symbol} @ trigger {stop_price}")
            
            # Binance spot uses stopLossLimit for stop orders
            params = {
                "stopPrice": stop_price,
                "type": "stop_loss_limit"
            }
            
            # Use slightly worse price to ensure execution
            limit_price = stop_price * 0.99 if side == SIDE_SELL else stop_price * 1.01
            
            order = self.client.create_order(
                symbol,
                "stop_loss_limit",
                side,
                amount,
                limit_price,
                params
            )
            
            return OrderResult(
                success=True,
                order_id=order.get("id"),
                symbol=symbol,
                side=side,
                amount=amount,
                price=limit_price,
                status=order.get("status", "open"),
                raw_response=order
            )
            
        except Exception as e:
            logger.error(f"Stop-loss order failed: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                symbol=symbol,
                side=side,
                amount=amount,
                price=stop_price,
                status="failed",
                error=str(e)
            )
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order."""
        try:
            self.client.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get list of open orders."""
        try:
            orders = self.client.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            return []
    
    def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Get status of a specific order."""
        try:
            order = self.client.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol."""
        try:
            ticker = self.client.fetch_ticker(symbol)
            return ticker["last"]
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            raise
