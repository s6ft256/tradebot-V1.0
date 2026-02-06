from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
import json

import httpx

if TYPE_CHECKING:
    from paid_trading_bot.core.types import Candle, Position


@dataclass
class GeminiConfig:
    """Configuration for Gemini AI integration."""
    api_key: str
    model: str = "gemini-1.5-flash"
    temperature: float = 0.3
    max_tokens: int = 1024
    timeout: float = 10.0


@dataclass
class AISignalReview:
    """AI review result for a trading signal."""
    approved: bool
    confidence: float
    reasoning: str
    risk_flags: list[str]
    recommendation: str


class GeminiSupervisoryLayer:
    """
    AI supervisory layer using Google's Gemini API.
    Reviews trading signals before execution for safety and quality.
    """

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, config: GeminiConfig):
        self._config = config
        self._client = httpx.AsyncClient(timeout=config.timeout)

    async def review_entry_signal(
        self,
        signal: dict,
        candles_1h: list[Candle],
        open_positions: list[Position],
        account_balance: float,
    ) -> AISignalReview:
        """
        Review a potential entry signal using Gemini AI.
        
        Returns approval decision with reasoning and risk flags.
        """
        # Prepare market context
        recent_candles = candles_1h[-20:] if len(candles_1h) >= 20 else candles_1h
        price_action = self._analyze_price_action(recent_candles)
        
        # Build prompt
        prompt = self._build_entry_review_prompt(
            signal=signal,
            price_action=price_action,
            open_positions_count=len(open_positions),
            account_balance=account_balance,
        )

        try:
            response = await self._call_gemini(prompt)
            parsed = self._parse_ai_response(response)
            
            return AISignalReview(
                approved=parsed.get("approved", False),
                confidence=parsed.get("confidence", 0.0),
                reasoning=parsed.get("reasoning", "No reasoning provided"),
                risk_flags=parsed.get("risk_flags", []),
                recommendation=parsed.get("recommendation", "hold"),
            )
        except Exception as e:
            # Fail-safe: reject on error
            return AISignalReview(
                approved=False,
                confidence=0.0,
                reasoning=f"AI review failed: {str(e)}",
                risk_flags=["ai_system_error"],
                recommendation="hold",
            )

    async def review_exit_signal(
        self,
        position: Position,
        current_price: float,
        candles_1h: list[Candle],
    ) -> AISignalReview:
        """Review a potential exit signal using Gemini AI."""
        unrealized_pnl = (current_price - position.entry_price) / position.entry_price * 100
        if position.side == "sell":
            unrealized_pnl = -unrealized_pnl

        prompt = self._build_exit_review_prompt(
            position=position,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            hold_time_hours=self._calculate_hold_time(position),
        )

        try:
            response = await self._call_gemini(prompt)
            parsed = self._parse_ai_response(response)
            
            return AISignalReview(
                approved=parsed.get("approved", False),
                confidence=parsed.get("confidence", 0.0),
                reasoning=parsed.get("reasoning", "No reasoning provided"),
                risk_flags=parsed.get("risk_flags", []),
                recommendation=parsed.get("recommendation", "hold"),
            )
        except Exception as e:
            return AISignalReview(
                approved=False,
                confidence=0.0,
                reasoning=f"AI review failed: {str(e)}",
                risk_flags=["ai_system_error"],
                recommendation="hold",
            )

    async def market_sentiment_analysis(
        self,
        symbol: str,
        candles_1h: list[Candle],
    ) -> dict:
        """Get AI market sentiment analysis."""
        price_action = self._analyze_price_action(candles_1h[-50:] if len(candles_1h) >= 50 else candles_1h)
        
        prompt = f"""
Analyze the market sentiment for {symbol} based on recent price action:

Price Statistics (last {len(candles_1h)} hours):
- Current: ${price_action['current']:.2f}
- 24h Change: {price_action['change_24h']:.2f}%
- 24h High: ${price_action['high_24h']:.2f}
- 24h Low: ${price_action['low_24h']:.2f}
- Volatility: {price_action['volatility']:.2f}%

Provide a JSON response with:
{{
    "sentiment": "bullish|bearish|neutral",
    "confidence": 0.0-1.0,
    "key_factors": ["factor1", "factor2"],
    "support_level": float,
    "resistance_level": float,
    "outlook": "short term outlook description"
}}
"""

        try:
            response = await self._call_gemini(prompt)
            return self._parse_sentiment_response(response)
        except Exception as e:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "key_factors": ["ai_error"],
                "support_level": price_action['low_24h'],
                "resistance_level": price_action['high_24h'],
                "outlook": f"Analysis failed: {str(e)}",
            }

    async def _call_gemini(self, prompt: str) -> str:
        """Make API call to Gemini."""
        url = self.GEMINI_API_URL.format(model=self._config.model)
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self._config.temperature,
                "maxOutputTokens": self._config.max_tokens,
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._config.api_key,
        }

        response = await self._client.post(
            url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract text from response
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                return candidate["content"]["parts"][0].get("text", "")
        
        return ""

    def _build_entry_review_prompt(
        self,
        signal: dict,
        price_action: dict,
        open_positions_count: int,
        account_balance: float,
    ) -> str:
        """Build prompt for entry signal review."""
        return f"""
You are a risk management AI for a cryptocurrency trading bot. Review this trade signal:

SIGNAL DETAILS:
- Symbol: {signal.get('symbol')}
- Side: {signal.get('side')}
- Confidence: {signal.get('confidence', 0):.2f}
- Strategy Reason: {signal.get('reason')}
- Suggested Stop: ${signal.get('suggested_stop', 0):.2f}
- Suggested Target: ${signal.get('suggested_target', 0):.2f}

MARKET CONTEXT:
- Current Price: ${price_action['current']:.2f}
- 24h Change: {price_action['change_24h']:.2f}%
- Volatility: {price_action['volatility']:.2f}%

ACCOUNT CONTEXT:
- Open Positions: {open_positions_count}
- Account Balance: ${account_balance:.2f}

Evaluate this trade for:
1. Risk/reward ratio (should be at least 1:1.5)
2. Stop loss placement (should be based on technical levels)
3. Position sizing appropriateness
4. Market volatility conditions
5. Overtrading concerns

Respond ONLY with valid JSON in this exact format:
{{
    "approved": true|false,
    "confidence": 0.0-1.0,
    "reasoning": "explanation in 1-2 sentences",
    "risk_flags": ["flag1", "flag2"],
    "recommendation": "approve|reject|reduce_size"
}}
"""

    def _build_exit_review_prompt(
        self,
        position: Position,
        current_price: float,
        unrealized_pnl: float,
        hold_time_hours: float,
    ) -> str:
        """Build prompt for exit signal review."""
        pnl_color = "profit" if unrealized_pnl > 0 else "loss"
        
        return f"""
You are a risk management AI for a cryptocurrency trading bot. Review this exit consideration:

POSITION DETAILS:
- Symbol: {position.symbol}
- Side: {position.side}
- Entry Price: ${position.entry_price:.2f}
- Current Price: ${current_price:.2f}
- Unrealized P&L: {unrealized_pnl:.2f}% ({pnl_color})
- Hold Time: {hold_time_hours:.1f} hours
- Stop Loss: ${position.stop_loss:.2f}
- Take Profit: ${position.take_profit:.2f}

Evaluate:
1. Is this exit premature or justified?
2. Are we cutting losses appropriately or taking profit too early?
3. Should we adjust stop loss to breakeven or trail profits?

Respond ONLY with valid JSON:
{{
    "approved": true|false,
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "risk_flags": ["flag1"],
    "recommendation": "exit|hold|adjust_stop"
}}
"""

    def _analyze_price_action(self, candles: list[Candle]) -> dict:
        """Analyze price action from candles."""
        if not candles:
            return {
                "current": 0,
                "change_24h": 0,
                "high_24h": 0,
                "low_24h": 0,
                "volatility": 0,
            }
        
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        
        current = closes[-1]
        open_24h = closes[0] if len(closes) > 0 else current
        change_24h = ((current - open_24h) / open_24h) * 100 if open_24h else 0
        
        return {
            "current": current,
            "change_24h": change_24h,
            "high_24h": max(highs),
            "low_24h": min(lows),
            "volatility": self._calculate_volatility(closes),
        }

    def _calculate_volatility(self, prices: list[float]) -> float:
        """Calculate price volatility as percentage."""
        if len(prices) < 2:
            return 0.0
        
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        return (std_dev / mean) * 100 if mean else 0.0

    def _calculate_hold_time(self, position: Position) -> float:
        """Calculate position hold time in hours."""
        import time
        if hasattr(position, 'entry_time'):
            return (time.time() - position.entry_time) / 3600
        return 0.0

    def _parse_ai_response(self, response: str) -> dict:
        """Parse JSON response from AI."""
        try:
            # Extract JSON from potential markdown
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            # Fallback parsing
            return {
                "approved": "true" in response.lower() and "false" not in response.lower().split("true")[-1],
                "confidence": 0.5,
                "reasoning": "Parse error - raw response",
                "risk_flags": ["parse_error"],
                "recommendation": "hold",
            }

    def _parse_sentiment_response(self, response: str) -> dict:
        """Parse sentiment analysis response."""
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "key_factors": ["parse_error"],
                "support_level": 0,
                "resistance_level": 0,
                "outlook": "Failed to parse AI response",
            }

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
