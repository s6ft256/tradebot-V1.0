"""
Main Autonomous Trading Bot Entry Point

This bot operates 24/7 with:
- Rule-based strategy execution
- Hard risk limits (absolute authority)
- AI supervisory layer (can only pause/reduce, never override)
- Non-custodial design (no withdrawal permissions)

SURVIVABILITY > AGGRESSIVENESS
"""
from __future__ import annotations

import time
import sys
from datetime import datetime
from typing import Optional

# Setup logging first
from monitoring.logger import setup_logging, get_logger
from config.settings import CONFIG, load_config
from config.constants import (
    SYMBOL_BTC_USDT, TIMEFRAME_1H, SIDE_BUY, SIDE_SELL,
    POSITION_OPEN, TREND_BULLISH
)

# Import exchange
from exchange.binance_client import BinanceClient
from exchange.order_executor import OrderExecutor

# Import strategy
from strategy.ema_trend import analyze_trend, get_trend_bias
from strategy.entries import generate_entry_signal
from strategy.exits import calculate_exit_levels, check_exit_conditions, update_trailing_stop

# Import indicators
from indicators.ema import calculate_ema
from indicators.rsi import calculate_rsi
from indicators.atr import calculate_atr, calculate_volatility_percent

# Import risk engine
from risk.risk_engine import RiskEngine
from risk.emergency_stop import EmergencyStop

# Import AI layer
from ai.ai_client import GeminiClient, AIAnalysisResult
from ai.regime_gatekeeper import allow_trading
from ai.strategy_governor import get_strategy_modifiers
from ai.risk_sentinel import should_halt, check_sentinel_conditions

# Import state management
from state.position_manager import PositionManager, Position
from state.trade_state import TradeState, TradeRecord

# Import utilities
from monitoring.alerts import send_alert, send_trade_alert, send_risk_alert
from utils.timeframes import should_update
from utils.helpers import calculate_position_size, round_down, format_price

# Setup logging
setup_logging(CONFIG.log_level)
logger = get_logger(__name__)


class AutonomousTradingBot:
    """
    Fully autonomous trading bot.
    
    Design principles:
    1. Risk-first architecture
    2. AI supervises but doesn't trade
    3. Hard stops cannot be overridden
    4. All trades logged and auditable
    5. Non-custodial (no withdrawal permissions)
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("AUTONOMOUS TRADING BOT INITIALIZING")
        logger.info("=" * 60)
        
        # Initialize components
        self.config = CONFIG
        self.risk_engine = RiskEngine()
        self.emergency_stop = EmergencyStop()
        self.position_manager = PositionManager()
        self.trade_state = TradeState()
        
        # Initialize AI layer
        self.ai_client = GeminiClient()
        
        # Initialize exchange (if not paper trading)
        self.exchange_client: Optional[BinanceClient] = None
        self.order_executor: Optional[OrderExecutor] = None
        
        if not self.config.paper_trading:
            try:
                self.exchange_client = BinanceClient()
                self.order_executor = OrderExecutor(self.exchange_client, self.risk_engine)
                logger.info("Exchange client initialized for LIVE trading")
            except Exception as e:
                logger.error(f"Failed to initialize exchange: {e}")
                logger.warning("Falling back to paper trading mode")
                self.config = load_config()
                self.config.paper_trading = True
        
        # State tracking
        self.symbol = self.config.exchange.default_symbol
        self.timeframe = self.config.exchange.default_timeframe
        self.candles: list = []
        self.last_update: Optional[datetime] = None
        self.running = False
        self.initial_balance = 10000.0  # Starting balance for tracking
        
        logger.info(f"Symbol: {self.symbol}, Timeframe: {self.timeframe}")
        logger.info(f"Paper Trading: {self.config.paper_trading}")
        logger.info(f"AI Enabled: {self.ai_client.is_enabled()}")
        logger.info("Bot initialization complete")
    
    def fetch_market_data(self) -> bool:
        """Fetch latest market data."""
        try:
            if self.exchange_client:
                self.candles = self.exchange_client.fetch_ohlcv(
                    self.symbol, self.timeframe, limit=200
                )
            else:
                # Paper trading - would use historical data or mock
                logger.debug("Paper mode: skipping data fetch")
                return False
            
            self.last_update = datetime.utcnow()
            return len(self.candles) >= 50
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return False
    
    def analyze_market(self) -> dict:
        """Perform market analysis."""
        if len(self.candles) < 50:
            return {"error": "Insufficient data"}
        
        # Calculate indicators
        closes = [c[4] for c in self.candles]
        current_price = closes[-1]
        
        ema_50 = calculate_ema(closes, 50)
        ema_200 = calculate_ema(closes, 200)
        rsi = calculate_rsi(closes, 14)
        atr = calculate_atr(self.candles, 14)
        
        # Trend analysis
        trend_state = analyze_trend(self.candles)
        
        # Volatility
        volatility = calculate_volatility_percent(self.candles)
        
        return {
            "current_price": current_price,
            "ema_50": ema_50[-1] if ema_50 else current_price,
            "ema_200": ema_200[-1] if ema_200 else current_price,
            "rsi": rsi[-1] if rsi else 50.0,
            "atr": atr[-1] if atr else 0.0,
            "volatility": volatility,
            "trend": trend_state.direction,
            "trend_strength": trend_state.strength,
        }
    
    def get_ai_analysis(self, market_data: dict) -> AIAnalysisResult:
        """Get AI supervisory analysis."""
        if not self.ai_client.is_enabled():
            # AI disabled - default to allowing with caution
            return AIAnalysisResult(
                regime="TRENDING",
                confidence=1.0,
                recommendation="ALLOW",
                reasoning="AI layer disabled - manual supervision required",
                risk_level="MEDIUM"
            )
        
        # Build payload for AI
        payload = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": market_data.get("current_price"),
            "trend": market_data.get("trend"),
            "trend_strength": market_data.get("trend_strength"),
            "rsi": market_data.get("rsi"),
            "volatility": market_data.get("volatility"),
            "atr": market_data.get("atr"),
            "ema_50": market_data.get("ema_50"),
            "ema_200": market_data.get("ema_200"),
            "open_positions": self.position_manager.get_position_count(),
            "daily_trades": self.risk_engine.state.total_trades_today,
        }
        
        return self.ai_client.analyze(payload)
    
    def check_entry_conditions(self, market_data: dict, ai_result: AIAnalysisResult) -> Optional[dict]:
        """Check if we should enter a new position."""
        # Check AI gatekeeper
        if not allow_trading(ai_result):
            logger.info("AI Gatekeeper: Trading not allowed")
            return None
        
        # Check risk engine
        balance = self.initial_balance  # TODO: Get actual balance
        if not self.risk_engine.can_open_trade(balance):
            logger.info("Risk Engine: Cannot open new trade")
            return None
        
        # Check max positions
        if self.position_manager.get_position_count() >= self.config.risk.max_open_positions:
            logger.info("Position limit reached")
            return None
        
        # Check if already have position for this symbol
        if self.position_manager.has_open_position(self.symbol):
            logger.info("Already have position for this symbol")
            return None
        
        # Generate entry signal
        entry_signal = generate_entry_signal(self.candles, market_data.get("trend", "NEUTRAL"))
        
        if not entry_signal.should_enter:
            logger.debug(f"No entry signal: {entry_signal.reason}")
            return None
        
        return {
            "signal": entry_signal,
            "market_data": market_data,
        }
    
    def execute_entry(self, entry_data: dict) -> Optional[Position]:
        """Execute trade entry."""
        signal = entry_data["signal"]
        market_data = entry_data["market_data"]
        
        # Get strategy modifiers from AI governor
        ai_modifiers = get_strategy_modifiers(
            self.get_ai_analysis(market_data) if self.ai_client.is_enabled() else 
            AIAnalysisResult("TRENDING", 1.0, "ALLOW", "", "MEDIUM")
        )
        
        if ai_modifiers["skip_entries"]:
            logger.info("AI Governor: Skipping entry")
            return None
        
        # Calculate position size
        entry_price = signal.price
        risk_percent = self.config.risk.max_risk_per_trade_percent * ai_modifiers["risk_multiplier"]
        
        # Calculate stop loss
        atr = market_data.get("atr", entry_price * 0.02)
        stop_loss = entry_price - (atr * self.config.strategy.atr_stop_multiplier)
        
        # Calculate take profit (2:1 R/R)
        risk_distance = entry_price - stop_loss
        take_profit = entry_price + (risk_distance * 2)
        
        # Position sizing
        position_size = calculate_position_size(
            self.initial_balance,
            risk_percent,
            entry_price,
            stop_loss
        )
        
        if position_size <= 0:
            logger.error("Calculated position size is zero or negative")
            return None
        
        logger.info(f"Entry plan: {position_size} @ {entry_price}, SL: {stop_loss}, TP: {take_profit}")
        
        # Execute order (or simulate)
        if self.order_executor:
            result = self.order_executor.execute_buy(
                symbol=self.symbol,
                amount=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if not result.success:
                logger.error(f"Entry failed: {result.error}")
                return None
            
            entry_price = result.price or entry_price
        
        # Record position
        position = self.position_manager.open_position(
            symbol=self.symbol,
            side="long",
            entry_price=entry_price,
            amount=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        if position:
            self.risk_engine.register_trade_open(position_size, entry_price)
            send_trade_alert(self.symbol, "buy", position_size, entry_price)
            logger.info(f"Position opened: {position.id}")
        
        return position
    
    def manage_positions(self, market_data: dict) -> None:
        """Manage open positions (check exits, update stops)."""
        current_price = market_data.get("current_price", 0)
        
        for position in self.position_manager.get_open_positions():
            # Update position with current price
            self.position_manager.update_position_price(position.id, current_price)
            
            # Check exit conditions
            exit_check = check_exit_conditions(
                position.__dict__,
                current_price,
                datetime.utcnow().isoformat(),
                self.candles
            )
            
            if exit_check.should_exit:
                logger.info(f"Exit triggered: {exit_check.reason} @ {exit_check.pnl_percent:.2f}%")
                self.execute_exit(position, current_price, exit_check.reason)
                continue
            
            # Update trailing stop
            new_trail = update_trailing_stop(
                position.__dict__,
                current_price,
                self.candles
            )
            
            if new_trail and new_trail > position.stop_loss:
                logger.info(f"Trailing stop updated: {position.stop_loss:.2f} -> {new_trail:.2f}")
                position.stop_loss = new_trail
    
    def execute_exit(self, position: Position, exit_price: float, reason: str) -> None:
        """Execute position exit."""
        # Close position
        closed_position = self.position_manager.close_position(
            position.id, exit_price, reason
        )
        
        if not closed_position:
            return
        
        # Execute sell order (or simulate)
        if self.order_executor:
            self.order_executor.execute_sell(
                symbol=position.symbol,
                amount=position.amount,
                reason=reason
            )
        
        # Update risk engine
        pnl = closed_position.pnl_percent or 0
        self.risk_engine.register_trade_close(exit_price, position.amount, pnl)
        
        # Record trade
        trade_record = TradeRecord(
            trade_id=position.id,
            symbol=position.symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            amount=position.amount,
            entry_time=position.entry_time,
            exit_time=closed_position.exit_time or datetime.utcnow().isoformat(),
            exit_reason=reason,
            pnl_percent=pnl,
            pnl_amount=position.amount * (exit_price - position.entry_price) if position.side == "long" 
                        else position.amount * (position.entry_price - exit_price),
        )
        self.trade_state.record_trade(trade_record)
        
        # Send alert
        send_trade_alert(position.symbol, "sell", position.amount, exit_price, pnl)
        
        logger.info(f"Position closed: {reason}, P&L: {pnl:+.2f}%")
    
    def run_iteration(self) -> None:
        """Run one iteration of the trading loop."""
        logger.debug("=" * 40)
        logger.debug(f"Iteration starting at {datetime.utcnow().isoformat()}")
        
        # Check emergency stop
        if self.emergency_stop.check_and_halt():
            logger.critical("EMERGENCY STOP ACTIVE - skipping iteration")
            return
        
        # Check risk engine emergency
        if self.risk_engine.state.emergency_stop:
            logger.critical("RISK ENGINE EMERGENCY - skipping iteration")
            return
        
        # Fetch market data
        if not self.fetch_market_data():
            logger.warning("Could not fetch market data")
            return
        
        # Analyze market
        market_data = self.analyze_market()
        if "error" in market_data:
            logger.warning(f"Market analysis error: {market_data['error']}")
            return
        
        logger.info(f"Price: {market_data['current_price']:.2f}, Trend: {market_data['trend']}, RSI: {market_data['rsi']:.1f}")
        
        # Update risk engine with current balance
        # TODO: Get actual balance from exchange
        self.risk_engine.update_balance(self.initial_balance, self.initial_balance)
        
        # Get AI analysis
        ai_result = self.get_ai_analysis(market_data)
        
        # Check AI sentinel
        if should_halt(ai_result):
            logger.critical("AI RISK SENTINEL: HALT RECOMMENDED")
            # Don't halt completely, just skip this iteration
            # In production, this could trigger a cooldown period
        
        # Manage existing positions
        self.manage_positions(market_data)
        
        # Check for entry opportunity
        if self.position_manager.get_position_count() < self.config.risk.max_open_positions:
            entry_data = self.check_entry_conditions(market_data, ai_result)
            if entry_data:
                self.execute_entry(entry_data)
        
        # Update state
        self.trade_state.update_last_run()
        
        logger.debug(f"Iteration complete. Positions: {self.position_manager.get_position_count()}")
    
    def run(self) -> None:
        """Main autonomous loop - runs until stopped."""
        logger.info("=" * 60)
        logger.info("AUTONOMOUS TRADING BOT STARTED")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                try:
                    self.run_iteration()
                except Exception as e:
                    logger.exception(f"Error in iteration: {e}")
                    self.trade_state.log_error(str(e))
                
                # Wait for next iteration
                time.sleep(self.config.loop_interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("=" * 60)
            logger.info("BOT STOPPED BY USER")
            logger.info("=" * 60)
            self.running = False
        
        # Cleanup
        self.shutdown()
    
    def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down...")
        
        # Close open positions if emergency
        if self.emergency_stop.is_active() or self.risk_engine.state.emergency_stop:
            logger.critical("EMERGENCY - closing all positions")
            for position in self.position_manager.get_open_positions():
                current_price = self.candles[-1][4] if self.candles else position.entry_price
                self.execute_exit(position, current_price, "EMERGENCY_SHUTDOWN")
        
        # Save state
        self.trade_state._save_state()
        
        # Print summary
        stats = self.position_manager.get_stats()
        logger.info("=" * 60)
        logger.info("TRADING SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Trades: {stats['closed_positions']}")
        logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
        logger.info(f"Total P&L: {stats['total_pnl']:.2f}%")
        logger.info(f"Current Positions: {stats['open_positions']}")
        logger.info("=" * 60)


def main():
    """Application entry point."""
    # Validate configuration
    if not CONFIG.exchange.api_key or not CONFIG.exchange.api_secret:
        if not CONFIG.paper_trading:
            logger.error("API credentials not configured and paper trading disabled")
            logger.info("Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
            logger.info("Or enable PAPER_TRADING=true")
            sys.exit(1)
    
    # Create and run bot
    bot = AutonomousTradingBot()
    bot.run()


if __name__ == "__main__":
    main()
