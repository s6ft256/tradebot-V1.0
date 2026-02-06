"""
Strategy Governor - adjusts strategy parameters based on AI recommendations.
"""
from __future__ import annotations

from ai.ai_client import AIAnalysisResult
from config.settings import CONFIG
from monitoring.logger import get_logger

logger = get_logger(__name__)


def adjust_risk(ai_output: AIAnalysisResult, base_risk: float) -> float:
    """
    Adjust position risk based on AI recommendation.
    
    Args:
        ai_output: AI analysis result
        base_risk: Base risk percentage (e.g., 1.0 for 1%)
        
    Returns:
        Adjusted risk percentage
    """
    if ai_output.recommendation == "REDUCE_RISK":
        reduced_risk = base_risk * 0.5
        logger.info(f"AI REDUCE_RISK: Adjusting risk from {base_risk}% to {reduced_risk}%")
        return reduced_risk
    
    if ai_output.recommendation == "HALT":
        logger.warning("AI HALT: Risk reduced to 0")
        return 0.0
    
    # ALLOW - use base risk
    return base_risk


def adjust_position_size(ai_output: AIAnalysisResult, base_size: float) -> float:
    """
    Adjust position size based on AI recommendation.
    
    Args:
        ai_output: AI analysis result
        base_size: Base position size
        
    Returns:
        Adjusted position size
    """
    if ai_output.recommendation == "REDUCE_RISK":
        reduced_size = base_size * 0.5
        logger.info(f"AI REDUCE_RISK: Adjusting position size from {base_size} to {reduced_size}")
        return reduced_size
    
    if ai_output.recommendation == "HALT":
        logger.warning("AI HALT: Position size set to 0")
        return 0.0
    
    return base_size


def get_strategy_modifiers(ai_output: AIAnalysisResult) -> dict:
    """
    Get all strategy modifiers based on AI output.
    
    Returns:
        Dict with adjusted parameters
    """
    base_risk = CONFIG.risk.max_risk_per_trade_percent
    
    modifiers = {
        "risk_multiplier": 1.0,
        "position_size_multiplier": 1.0,
        "tighten_stops": False,
        "reduce_targets": False,
        "skip_entries": False,
    }
    
    if ai_output.recommendation == "HALT":
        modifiers["risk_multiplier"] = 0.0
        modifiers["position_size_multiplier"] = 0.0
        modifiers["skip_entries"] = True
        
    elif ai_output.recommendation == "REDUCE_RISK":
        modifiers["risk_multiplier"] = 0.5
        modifiers["position_size_multiplier"] = 0.5
        modifiers["tighten_stops"] = True
        modifiers["reduce_targets"] = True
        
    elif ai_output.risk_level == "HIGH":
        modifiers["risk_multiplier"] = 0.7
        modifiers["tighten_stops"] = True
        
    elif ai_output.risk_level == "EXTREME":
        modifiers["risk_multiplier"] = 0.0
        modifiers["skip_entries"] = True
    
    adjusted_risk = base_risk * modifiers["risk_multiplier"]
    logger.info(f"Strategy modifiers applied: risk={adjusted_risk:.2f}%, skip_entries={modifiers['skip_entries']}")
    
    return modifiers
