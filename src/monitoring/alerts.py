"""
Alert system for critical notifications.
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime

from monitoring.logger import get_logger

logger = get_logger(__name__)


def send_alert(message: str, level: str = "WARNING") -> None:
    """
    Send an alert notification.
    
    In production, this could send:
    - Email notifications
    - Slack/Discord messages
    - SMS alerts
    - Push notifications
    
    For now, we just log critical alerts.
    """
    timestamp = datetime.utcnow().isoformat()
    alert_msg = f"[{level}] {timestamp}: {message}"
    
    # Log the alert
    if level == "CRITICAL":
        logger.critical(alert_msg)
    elif level == "WARNING":
        logger.warning(alert_msg)
    else:
        logger.info(alert_msg)
    
    # TODO: Implement actual notification channels
    # - Email
    # - Slack webhook
    # - Discord webhook
    # - SMS via Twilio


def send_trade_alert(symbol: str, side: str, amount: float, price: float, pnl: Optional[float] = None) -> None:
    """Send trade execution alert."""
    msg = f"TRADE: {side.upper()} {amount} {symbol} @ {price}"
    if pnl is not None:
        msg += f" | P&L: {pnl:+.2f}%"
    
    send_alert(msg, level="INFO")


def send_risk_alert(reason: str) -> None:
    """Send risk-related alert."""
    send_alert(f"RISK: {reason}", level="CRITICAL")


def send_ai_alert(recommendation: str, reasoning: str) -> None:
    """Send AI recommendation alert."""
    send_alert(f"AI: {recommendation} - {reasoning}", level="WARNING")
