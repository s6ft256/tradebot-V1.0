"""
Risk Sentinel - AI-powered risk monitoring and halt detection.
"""
from __future__ import annotations

from ai.ai_client import AIAnalysisResult
from monitoring.logger import get_logger
from monitoring.alerts import send_alert

logger = get_logger(__name__)


def should_halt(ai_output: AIAnalysisResult) -> bool:
    """
    Determine if trading should be halted immediately.
    
    Args:
        ai_output: AI analysis result
        
    Returns:
        True if trading must halt
    """
    # Explicit HALT recommendation
    if ai_output.recommendation == "HALT":
        logger.critical(f"AI HALT triggered: {ai_output.reasoning}")
        send_alert(f"Risk Sentinel HALT: {ai_output.reasoning}")
        return True
    
    # Extreme risk level
    if ai_output.risk_level == "EXTREME":
        logger.critical("EXTREME risk level detected - halting")
        send_alert("Risk Sentinel: EXTREME risk - trading halted")
        return True
    
    # Unknown regime with low confidence
    if ai_output.regime == "UNKNOWN" and ai_output.confidence < 0.3:
        logger.warning("Unknown market regime with low confidence - halting")
        return True
    
    return False


def check_sentinel_conditions(
    ai_output: AIAnalysisResult,
    current_drawdown: float,
    daily_loss_percent: float,
) -> dict:
    """
    Comprehensive sentinel check combining AI and hard metrics.
    
    Args:
        ai_output: AI analysis
        current_drawdown: Current drawdown percentage
        daily_loss_percent: Daily loss percentage
        
    Returns:
        Dict with halt decision and details
    """
    halt_reasons = []
    
    # AI-based checks
    if ai_output.recommendation == "HALT":
        halt_reasons.append(f"AI_HALT: {ai_output.reasoning}")
    
    if ai_output.risk_level == "EXTREME":
        halt_reasons.append("EXTREME_RISK_LEVEL")
    
    # Hard metric checks
    if current_drawdown > 15:
        halt_reasons.append(f"HIGH_DRAWDOWN: {current_drawdown:.2f}%")
    
    if daily_loss_percent > 5:
        halt_reasons.append(f"DAILY_LOSS_SPIKE: {daily_loss_percent:.2f}%")
    
    should_halt_now = len(halt_reasons) > 0
    
    if should_halt_now:
        logger.critical(f"Risk Sentinel HALT: {', '.join(halt_reasons)}")
    
    return {
        "should_halt": should_halt_now,
        "reasons": halt_reasons,
        "ai_recommendation": ai_output.recommendation,
        "ai_risk_level": ai_output.risk_level,
        "drawdown": current_drawdown,
        "daily_loss": daily_loss_percent
    }
