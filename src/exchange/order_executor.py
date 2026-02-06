"""
Order executor - handles buy/sell execution with risk checks.
"""
from __future__ import annotations

from typing import Optional
from dataclasses import dataclass

from exchange.binance_client import BinanceClient, OrderResult
from config.settings import CONFIG
from config.constants import SIDE_BUY, SIDE_SELL
from risk.risk_engine import RiskEngine
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionPlan:
    """Plan for order execution."""
    symbol: str
    side: str
    amount: float
    price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]


class OrderExecutor:
    """
    Executes orders with pre-trade risk validation.
    
    All orders must pass risk checks before execution.
    """
    
    def __init__(self, client: BinanceClient, risk_engine: RiskEngine):
        self.client = client
        self.risk_engine = risk_engine
        self.paper_trading = CONFIG.paper_trading
        
        logger.info(f"OrderExecutor initialized (paper_trading={self.paper_trading})")
    
    def execute_buy(
        self,
        symbol: str,
        amount: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> OrderResult:
        """
        Execute buy order with risk validation.
        
        Args:
            symbol: Trading pair
            amount: Position size
            price: Limit price (None for market)
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        # Pre-trade risk check
        if not self.risk_engine.can_open_trade(self._get_account_balance()):
            logger.warning("Risk engine blocked buy order")
            return OrderResult(
                success=False,
                order_id=None,
                symbol=symbol,
                side=SIDE_BUY,
                amount=amount,
                price=price,
                status="blocked_by_risk",
                error="Risk engine blocked order"
            )
        
        if self.paper_trading:
            return self._simulate_order(symbol, SIDE_BUY, amount, price)
        
        # Execute real order
        if price:
            result = self.client.place_limit_order(symbol, SIDE_BUY, amount, price)
        else:
            result = self.client.place_market_order(symbol, SIDE_BUY, amount)
        
        if result.success and stop_loss:
            # Place stop loss order
            self.client.place_stop_loss_order(symbol, SIDE_SELL, amount, stop_loss)
        
        if result.success:
            self.risk_engine.register_trade_open(amount, price or result.price)
        
        return result
    
    def execute_sell(
        self,
        symbol: str,
        amount: float,
        price: Optional[float] = None,
        reason: str = "manual"
    ) -> OrderResult:
        """Execute sell order to close position."""
        if self.paper_trading:
            result = self._simulate_order(symbol, SIDE_SELL, amount, price)
        else:
            if price:
                result = self.client.place_limit_order(symbol, SIDE_SELL, amount, price)
            else:
                result = self.client.place_market_order(symbol, SIDE_SELL, amount)
        
        if result.success:
            self.risk_engine.register_trade_close(result.price or price, amount)
            logger.info(f"Position closed: {reason}")
        
        return result
    
    def _simulate_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float]
    ) -> OrderResult:
        """Simulate order execution for paper trading."""
        current_price = price or self.client.get_current_price(symbol)
        
        logger.info(f"[PAPER] Simulated {side}: {amount} {symbol} @ {current_price}")
        
        return OrderResult(
            success=True,
            order_id=f"paper_{id(self)}_{side}",
            symbol=symbol,
            side=side,
            amount=amount,
            price=current_price,
            status="filled",
            error=None
        )
    
    def _get_account_balance(self) -> float:
        """Get account balance for risk calculations."""
        try:
            balance = self.client.get_balance("USDT")
            if isinstance(balance, dict):
                return balance.get("USDT", {}).get("free", 0)
            return balance.free
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
