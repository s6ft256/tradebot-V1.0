"""
Gemini AI client - supervisory intelligence layer.
"""
from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
import google.generativeai as genai

from config.settings import CONFIG
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIAnalysisResult:
    """Result from AI analysis."""
    regime: str  # TRENDING | CHOPPY | RANGING | VOLATILE
    confidence: float  # 0.0 to 1.0
    recommendation: str  # ALLOW | REDUCE_RISK | HALT
    reasoning: str
    risk_level: str  # LOW | MEDIUM | HIGH | EXTREME
    raw_response: Optional[Dict] = None


class GeminiClient:
    """
    Gemini AI client for market analysis and risk supervision.
    
    IMPORTANT: AI is SUPERVISORY ONLY - it cannot:
    - Predict prices
    - Override risk rules
    - Execute trades
    - Recommend aggressive sizing
    
    AI can only:
    - Recommend ALLOW / REDUCE_RISK / HALT
    - Assess market regime
    - Flag unusual conditions
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize Gemini client."""
        self.api_key = api_key or CONFIG.ai.gemini_api_key
        self.model_name = model or CONFIG.ai.gemini_model
        
        if not self.api_key:
            logger.warning("No Gemini API key configured - AI layer disabled")
            self._enabled = False
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self._enabled = True
            logger.info(f"Gemini client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if AI client is enabled."""
        return self._enabled
    
    def analyze(self, payload: Dict[str, Any]) -> AIAnalysisResult:
        """
        Analyze market conditions and provide supervisory recommendation.
        
        Input payload should contain:
        - price_data: recent prices
        - indicators: RSI, EMA, ATR values
        - volatility: current volatility measure
        - trend: current trend direction
        - recent_trades: recent trade outcomes
        
        Returns:
            AIAnalysisResult with regime, confidence, recommendation
        """
        if not self._enabled:
            return AIAnalysisResult(
                regime="TRENDING",
                confidence=1.0,
                recommendation="ALLOW",
                reasoning="AI disabled - defaulting to allow",
                risk_level="MEDIUM"
            )
        
        try:
            prompt = self._build_prompt(payload)
            response = self.model.generate_content(prompt)
            
            # Parse response
            result = self._parse_response(response.text)
            logger.info(f"AI Analysis: {result.recommendation} | Regime: {result.regime} | Confidence: {result.confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return AIAnalysisResult(
                regime="UNKNOWN",
                confidence=0.0,
                recommendation="HALT",  # Fail safe
                reasoning=f"AI analysis error: {e}",
                risk_level="HIGH"
            )
    
    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        """Build analysis prompt with embedded constraints."""
        
        system_prompt = """You are a supervisory risk intelligence for a cryptocurrency trading bot.

YOUR ROLE:
- Analyze market conditions to recommend trading posture
- Protect capital by identifying dangerous market conditions
- You are NOT a trader - you only supervise

CONSTRAINTS (NEVER VIOLATE):
1. You CANNOT predict future prices
2. You CANNOT bypass risk rules
3. You CANNOT recommend position sizing
4. You CANNOT override stop losses
5. You CANNOT recommend aggressive behavior

YOU MAY ONLY RECOMMEND ONE OF:
- "ALLOW" - Market conditions suitable for trading
- "REDUCE_RISK" - Market uncertain, reduce activity
- "HALT" - Market dangerous, stop trading

ANALYZE THE FOLLOWING MARKET DATA AND RESPOND WITH JSON ONLY:

{
    "regime": "TRENDING|CHOPPY|RANGING|VOLATILE",
    "confidence": 0.0-1.0,
    "recommendation": "ALLOW|REDUCE_RISK|HALT",
    "risk_level": "LOW|MEDIUM|HIGH|EXTREME",
    "reasoning": "Brief explanation of your assessment"
}

Market Data:
"""
        
        # Add market data
        data_str = json.dumps(payload, indent=2)
        return system_prompt + data_str
    
    def _parse_response(self, text: str) -> AIAnalysisResult:
        """Parse AI response text into structured result."""
        try:
            # Extract JSON from response
            # Handle cases where model adds markdown or extra text
            json_start = text.find("{")
            json_end = text.rfind("}")
            
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON found in response")
            
            json_str = text[json_start:json_end+1]
            data = json.loads(json_str)
            
            # Validate and sanitize
            recommendation = data.get("recommendation", "HALT").upper()
            if recommendation not in ["ALLOW", "REDUCE_RISK", "HALT"]:
                recommendation = "HALT"  # Fail safe
            
            regime = data.get("regime", "UNKNOWN").upper()
            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            
            risk_level = data.get("risk_level", "HIGH").upper()
            
            return AIAnalysisResult(
                regime=regime,
                confidence=confidence,
                recommendation=recommendation,
                reasoning=data.get("reasoning", "No reasoning provided"),
                risk_level=risk_level,
                raw_response=data
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return AIAnalysisResult(
                regime="UNKNOWN",
                confidence=0.0,
                recommendation="HALT",
                reasoning=f"Parse error: {e}",
                risk_level="HIGH"
            )
