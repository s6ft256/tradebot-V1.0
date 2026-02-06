"""
Regime Gatekeeper - determines if market conditions allow trading.
"""
from __future__ import annotations

from ai.ai_client import AIAnalysisResult
from config.settings import CONFIG
from monitoring.logger import get_logger

logger = get_logger(__name__)


def allow_trading(ai_output: AIAnalysisResult) -> bool:
    """
    Determine if trading should be allowed based on AI analysis.
    
    Rules:
    - MUST be trending regime
    - Confidence MUST be above threshold
    - Recommendation MUST be ALLOW
    
    Args:
        ai_output: AI analysis result
        
    Returns:
        True if trading allowed, False otherwise
    """
    # Check if AI is disabled
    if ai_output.confidence == 1.0 and ai_output.reasoning == "AI disabled - defaulting to allow":
        logger.info("AI disabled - allowing trading (use with caution)")
        return True
    
    # Check recommendation
    if ai_output.recommendation == "HALT":
        logger.warning(f"AI HALT recommendation: {ai_output.reasoning}")
        return False
    
    if ai_output.recommendation == "REDUCE_RISK":
        logger.warning(f"AI REDUCE_RISK recommendation: {ai_output.reasoning}")
        # Still allow but with reduced size (handled elsewhere)
        return True
    
    # Check regime
    if ai_output.regime not in ["TRENDING"]:
        logger.warning(f"Non-trending regime: {ai_output.regime}")
        return False
    
    # Check confidence threshold
    threshold = CONFIG.ai.regime_confidence_threshold
    if ai_output.confidence < threshold:
        logger.warning(f"Confidence too low: {ai_output.confidence:.2f} < {threshold}")
        return False
    
    logger.info(f"Trading ALLOWED: {ai_output.regime} regime, confidence={ai_output.confidence:.2f}")
    return True


def get_regime_status(ai_output: AIAnalysisResult) -> dict:
    """Get detailed regime status for logging/monitoring."""
    return {
        "regime": ai_output.regime,
        "confidence": ai_output.confidence,
        "recommendation": ai_output.recommendation,
        "risk_level": ai_output.risk_level,
        "trading_allowed": allow_trading(ai_output),
        "reasoning": ai_output.reasoning
    }
