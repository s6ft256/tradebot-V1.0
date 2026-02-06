from paid_trading_bot.risk.limits import HardRiskLimits
from paid_trading_bot.risk.position_sizer import calculate_position_size


def test_position_size_basic():
    size = calculate_position_size(
        account_balance=1000.0,
        risk_percent=1.0,
        entry_price=100.0,
        stop_loss_price=99.0,
        ai_risk_multiplier=1.0,
    )
    # risk_amount = 10, stop_distance=1 => 10 units
    assert size == 10.0


def test_position_size_caps_risk_percent():
    limits = HardRiskLimits(max_risk_per_trade_percent=1.0)
    size = calculate_position_size(
        account_balance=1000.0,
        risk_percent=5.0,
        entry_price=100.0,
        stop_loss_price=99.0,
        ai_risk_multiplier=1.0,
        hard_limits=limits,
    )
    assert size == 10.0


def test_position_size_ai_can_only_reduce():
    size = calculate_position_size(
        account_balance=1000.0,
        risk_percent=1.0,
        entry_price=100.0,
        stop_loss_price=99.0,
        ai_risk_multiplier=2.0,
    )
    assert size == 10.0

    size2 = calculate_position_size(
        account_balance=1000.0,
        risk_percent=1.0,
        entry_price=100.0,
        stop_loss_price=99.0,
        ai_risk_multiplier=0.5,
    )
    assert size2 == 5.0
