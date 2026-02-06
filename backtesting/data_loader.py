from __future__ import annotations

from dataclasses import dataclass

from paid_trading_bot.core.types import Candle


@dataclass(frozen=True)
class HistoricalDataset:
    candles_1h: list[Candle]
    candles_5m: list[Candle]


class DataLoader:
    def __init__(self):
        pass

    def load_from_csv(self, *, path_1h: str, path_5m: str) -> HistoricalDataset:
        # Stub: implement CSV parsing in a later iteration.
        raise NotImplementedError("CSV loading not implemented yet")
