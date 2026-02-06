from datetime import datetime

from paid_trading_bot.core.types import Position, TradeSide
from paid_trading_bot.strategy.exit_logic import manage_exit


def test_exit_stop_loss_long():
    pos = Position(
        id="1",
        symbol="BTC/USDT",
        side=TradeSide.LONG,
        entry_price=100.0,
        stop_loss=99.0,
        take_profit_1=101.0,
        take_profit_2=102.0,
        entry_atr=1.0,
        size=1.0,
        opened_at=datetime.utcnow(),
        tp1_hit=False,
        highest_price=101.0,
    )
    sig = manage_exit(position=pos, current_price=98.9)
    assert sig is not None
    assert sig.exit_type == "STOP_LOSS"
