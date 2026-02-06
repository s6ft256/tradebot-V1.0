"""
Position Manager - tracks and manages open positions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from uuid import uuid4

from monitoring.logger import get_logger
from config.constants import POSITION_OPEN, POSITION_CLOSED

logger = get_logger(__name__)


@dataclass
class Position:
    """Represents an open trading position."""
    id: str
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    amount: float
    stop_loss: float
    take_profit: float
    entry_time: str
    status: str = POSITION_OPEN
    
    # Dynamic tracking
    highest_price: float = field(default=0.0)
    lowest_price: float = field(default=float('inf'))
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    exit_reason: Optional[str] = None
    pnl_percent: Optional[float] = None
    
    # Associated orders
    entry_order_id: Optional[str] = None
    stop_order_id: Optional[str] = None


class PositionManager:
    """
    Manages open positions and their lifecycle.
    """
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}  # id -> Position
        self.closed_positions: List[Position] = []
        self.max_positions = 2  # From risk config
        
        logger.info("PositionManager initialized")
    
    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        amount: float,
        stop_loss: float,
        take_profit: float,
        entry_order_id: Optional[str] = None,
    ) -> Optional[Position]:
        """
        Open a new position.
        
        Returns:
            Position object or None if max positions reached
        """
        # Check position limit
        open_count = len([p for p in self.positions.values() if p.status == POSITION_OPEN])
        if open_count >= self.max_positions:
            logger.warning(f"Max positions reached ({open_count}/{self.max_positions})")
            return None
        
        position = Position(
            id=str(uuid4())[:8],
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            amount=amount,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.utcnow().isoformat(),
            highest_price=entry_price,
            lowest_price=entry_price,
            entry_order_id=entry_order_id,
        )
        
        self.positions[position.id] = position
        logger.info(f"Position opened: {position.id} {side} {amount} {symbol} @ {entry_price}")
        
        return position
    
    def close_position(
        self,
        position_id: str,
        exit_price: float,
        exit_reason: str,
    ) -> Optional[Position]:
        """Close an open position."""
        position = self.positions.get(position_id)
        if not position or position.status != POSITION_OPEN:
            return None
        
        position.status = POSITION_CLOSED
        position.exit_price = exit_price
        position.exit_time = datetime.utcnow().isoformat()
        position.exit_reason = exit_reason
        
        # Calculate P&L
        if position.side == "long":
            position.pnl_percent = (exit_price - position.entry_price) / position.entry_price * 100
        else:
            position.pnl_percent = (position.entry_price - exit_price) / position.entry_price * 100
        
        # Move to closed
        self.closed_positions.append(position)
        
        logger.info(f"Position closed: {position_id} {exit_reason} P&L: {position.pnl_percent:.2f}%")
        
        return position
    
    def update_position_price(self, position_id: str, current_price: float) -> None:
        """Update position with current market price."""
        position = self.positions.get(position_id)
        if not position or position.status != POSITION_OPEN:
            return
        
        # Update highest/lowest prices
        if current_price > position.highest_price:
            position.highest_price = current_price
        if current_price < position.lowest_price:
            position.lowest_price = current_price
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions."""
        return [p for p in self.positions.values() if p.status == POSITION_OPEN]
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID."""
        return self.positions.get(position_id)
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if there's an open position for symbol."""
        return any(
            p.symbol == symbol and p.status == POSITION_OPEN
            for p in self.positions.values()
        )
    
    def get_position_count(self) -> int:
        """Get number of open positions."""
        return len([p for p in self.positions.values() if p.status == POSITION_OPEN])
    
    def get_total_pnl(self) -> float:
        """Get total realized P&L from closed positions."""
        return sum(p.pnl_percent or 0 for p in self.closed_positions)
    
    def get_open_pnl(self, current_prices: Dict[str, float]) -> float:
        """Calculate unrealized P&L for open positions."""
        total_pnl = 0.0
        for position in self.get_open_positions():
            current_price = current_prices.get(position.symbol)
            if not current_price:
                continue
            
            if position.side == "long":
                pnl = (current_price - position.entry_price) / position.entry_price * 100
            else:
                pnl = (position.entry_price - current_price) / position.entry_price * 100
            
            total_pnl += pnl
        
        return total_pnl
    
    def get_stats(self) -> dict:
        """Get position statistics."""
        closed = self.closed_positions
        winners = [p for p in closed if (p.pnl_percent or 0) > 0]
        losers = [p for p in closed if (p.pnl_percent or 0) <= 0]
        
        return {
            "open_positions": len(self.get_open_positions()),
            "closed_positions": len(closed),
            "total_pnl": self.get_total_pnl(),
            "win_count": len(winners),
            "loss_count": len(losers),
            "win_rate": len(winners) / len(closed) * 100 if closed else 0,
        }
