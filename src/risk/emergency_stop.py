"""
Emergency stop - hard kill switch for the trading bot.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from monitoring.logger import get_logger
from monitoring.alerts import send_alert

logger = get_logger(__name__)


@dataclass
class EmergencyStopState:
    """Emergency stop state."""
    is_active: bool = False
    triggered_at: Optional[datetime] = None
    reason: Optional[str] = None
    triggered_by: Optional[str] = None  # 'manual', 'risk_engine', 'circuit_breaker'
    recovery_attempts: int = 0


class EmergencyStop:
    """
    Emergency stop system - hard kill switch.
    
    When activated, ALL trading activity must cease immediately.
    """
    
    def __init__(self):
        self.state = EmergencyStopState()
        self._history: List[dict] = []
        logger.info("EmergencyStop initialized")
    
    def trigger(self, reason: str, triggered_by: str = "unknown") -> bool:
        """
        Trigger emergency stop.
        
        Args:
            reason: Why emergency stop was triggered
            triggered_by: What component triggered it
            
        Returns:
            True if newly triggered, False if already active
        """
        if self.state.is_active:
            logger.warning(f"Emergency stop already active: {self.state.reason}")
            return False
        
        self.state.is_active = True
        self.state.triggered_at = datetime.utcnow()
        self.state.reason = reason
        self.state.triggered_by = triggered_by
        
        # Log and alert
        logger.critical(f"EMERGENCY STOP TRIGGERED by {triggered_by}: {reason}")
        send_alert(f"EMERGENCY STOP: {reason}")
        
        # Record in history
        self._history.append({
            "time": datetime.utcnow().isoformat(),
            "reason": reason,
            "triggered_by": triggered_by,
            "type": "trigger"
        })
        
        return True
    
    def release(self, password: str, released_by: str) -> bool:
        """
        Release emergency stop (requires password).
        
        Args:
            password: Release password
            released_by: Who is releasing it
            
        Returns:
            True if released, False if invalid password or not active
        """
        if not self.state.is_active:
            return False
        
        # Password check (use secure method in production)
        if password != "EMERGENCY_RELEASE":
            logger.error(f"Invalid emergency release password attempt by {released_by}")
            return False
        
        self.state.is_active = False
        self.state.recovery_attempts += 1
        
        logger.critical(f"EMERGENCY STOP RELEASED by {released_by}")
        send_alert(f"Emergency stop released by {released_by}")
        
        self._history.append({
            "time": datetime.utcnow().isoformat(),
            "released_by": released_by,
            "recovery_count": self.state.recovery_attempts,
            "type": "release"
        })
        
        return True
    
    def is_active(self) -> bool:
        """Check if emergency stop is currently active."""
        return self.state.is_active
    
    def check_and_halt(self) -> bool:
        """
        Check if trading should halt.
        
        Returns:
            True if should halt (emergency active)
        """
        if self.state.is_active:
            logger.critical(f"HALT: Emergency stop active - {self.state.reason}")
            return True
        return False
    
    def get_status(self) -> dict:
        """Get emergency stop status."""
        return {
            "is_active": self.state.is_active,
            "reason": self.state.reason,
            "triggered_at": self.state.triggered_at.isoformat() if self.state.triggered_at else None,
            "triggered_by": self.state.triggered_by,
            "recovery_attempts": self.state.recovery_attempts,
            "history": self._history[-10:]  # Last 10 events
        }
