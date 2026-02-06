from __future__ import annotations

from paid_trading_bot.core.types import ExitSignal, Position, TradeSide


def manage_exit(*, position: Position, current_price: float) -> ExitSignal | None:
    if position.side == TradeSide.LONG:
        if current_price <= position.stop_loss:
            return ExitSignal(
                position_id=position.id,
                exit_type="STOP_LOSS",
                exit_price=current_price,
                size_percent=100.0,
            )

        if (not position.tp1_hit) and current_price >= position.take_profit_1:
            return ExitSignal(
                position_id=position.id,
                exit_type="TAKE_PROFIT_1",
                exit_price=current_price,
                size_percent=50.0,
            )

        if position.tp1_hit and position.highest_price is not None:
            trailing_stop = position.highest_price - (1.0 * position.entry_atr)
            if current_price <= trailing_stop:
                return ExitSignal(
                    position_id=position.id,
                    exit_type="TRAILING_STOP",
                    exit_price=current_price,
                    size_percent=100.0,
                )

    if position.side == TradeSide.SHORT:
        if current_price >= position.stop_loss:
            return ExitSignal(
                position_id=position.id,
                exit_type="STOP_LOSS",
                exit_price=current_price,
                size_percent=100.0,
            )

        if (not position.tp1_hit) and current_price <= position.take_profit_1:
            return ExitSignal(
                position_id=position.id,
                exit_type="TAKE_PROFIT_1",
                exit_price=current_price,
                size_percent=50.0,
            )

        if position.tp1_hit and position.lowest_price is not None:
            trailing_stop = position.lowest_price + (1.0 * position.entry_atr)
            if current_price >= trailing_stop:
                return ExitSignal(
                    position_id=position.id,
                    exit_type="TRAILING_STOP",
                    exit_price=current_price,
                    size_percent=100.0,
                )

    return None
