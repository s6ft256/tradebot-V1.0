"""
Trade state - persistent storage for trade history and state.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TradeRecord:
    """Record of a completed trade."""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    amount: float
    entry_time: str
    exit_time: str
    exit_reason: str
    pnl_percent: float
    pnl_amount: float
    fees: float = 0.0


class TradeState:
    """
    Persistent state storage for trades and bot state.
    """
    
    def __init__(self, storage_path: str = "data/trade_state.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.trades: List[TradeRecord] = []
        self.daily_stats: Dict = {}
        self.bot_state: Dict = {
            "started_at": datetime.utcnow().isoformat(),
            "last_run": None,
            "total_trades": 0,
            "errors": [],
        }
        
        self._load_state()
        logger.info("TradeState initialized")
    
    def record_trade(self, trade: TradeRecord) -> None:
        """Record a completed trade."""
        self.trades.append(trade)
        self.bot_state["total_trades"] = len(self.trades)
        self._save_state()
        
        logger.info(f"Trade recorded: {trade.trade_id} P&L: {trade.pnl_percent:.2f}%")
    
    def update_daily_stats(self, date: str, stats: dict) -> None:
        """Update statistics for a specific day."""
        self.daily_stats[date] = stats
        self._save_state()
    
    def get_daily_stats(self, date: Optional[str] = None) -> dict:
        """Get statistics for a specific day or current day."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        return self.daily_stats.get(date, {
            "trades": 0,
            "pnl": 0.0,
            "wins": 0,
            "losses": 0
        })
    
    def log_error(self, error: str) -> None:
        """Log an error occurrence."""
        self.bot_state["errors"].append({
            "time": datetime.utcnow().isoformat(),
            "error": error
        })
        # Keep only last 100 errors
        self.bot_state["errors"] = self.bot_state["errors"][-100:]
        self._save_state()
    
    def update_last_run(self) -> None:
        """Update last run timestamp."""
        self.bot_state["last_run"] = datetime.utcnow().isoformat()
        self._save_state()
    
    def get_all_trades(self) -> List[TradeRecord]:
        """Get all recorded trades."""
        return self.trades
    
    def get_recent_trades(self, count: int = 10) -> List[TradeRecord]:
        """Get recent trades."""
        return self.trades[-count:]
    
    def _save_state(self) -> None:
        """Save state to disk."""
        data = {
            "trades": [asdict(t) for t in self.trades],
            "daily_stats": self.daily_stats,
            "bot_state": self.bot_state,
            "saved_at": datetime.utcnow().isoformat(),
        }
        
        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(self) -> None:
        """Load state from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            # Load trades
            for trade_data in data.get("trades", []):
                self.trades.append(TradeRecord(**trade_data))
            
            # Load stats and state
            self.daily_stats = data.get("daily_stats", {})
            self.bot_state = data.get("bot_state", self.bot_state)
            
            logger.info(f"Loaded {len(self.trades)} trades from state")
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
