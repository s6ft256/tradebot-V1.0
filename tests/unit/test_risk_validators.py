from datetime import datetime

from paid_trading_bot.core.types import AccountState, TradeRequest, TradeSide
from paid_trading_bot.risk.limits import HardRiskLimits
from paid_trading_bot.risk.validators import validate_trade_request


def _base_request() -> TradeRequest:
    return TradeRequest(
        symbol="BTC/USDT",
        side=TradeSide.LONG,
        entry_price=100.0,
        stop_loss=99.0,
        position_size=10.0,
        timestamp=datetime.utcnow(),
    )


def _base_state() -> AccountState:
    return AccountState(
        balance=1000.0,
        daily_pnl_percent=0.0,
        current_drawdown_percent=0.0,
        consecutive_losses=0,
        open_positions=0,
        trades_today=0,
    )


def test_validate_trade_request_passes():
    limits = HardRiskLimits(max_risk_per_trade_percent=1.0)
    res = validate_trade_request(request=_base_request(), account_state=_base_state(), risk_limits=limits)
    assert res.approved is True


def test_validate_trade_request_daily_loss_cap_hits():
    limits = HardRiskLimits(daily_loss_cap_percent=3.0)
    state = _base_state()
    state.daily_pnl_percent = -3.0
    res = validate_trade_request(request=_base_request(), account_state=state, risk_limits=limits)
    assert res.approved is False
    assert res.reason == "DAILY_LOSS_CAP_HIT"


def test_validate_trade_request_risk_per_trade_exceeded():
    limits = HardRiskLimits(max_risk_per_trade_percent=0.5)
    res = validate_trade_request(request=_base_request(), account_state=_base_state(), risk_limits=limits)
    assert res.approved is False
    assert res.reason == "RISK_PER_TRADE_EXCEEDED"
