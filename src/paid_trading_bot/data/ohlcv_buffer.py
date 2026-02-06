from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from paid_trading_bot.core.types import Candle


@dataclass
class OHLCVBufferConfig:
    maxlen: int


class OHLCVBuffer:
    def __init__(self, config: OHLCVBufferConfig):
        if config.maxlen <= 0:
            raise ValueError("maxlen must be > 0")
        self._config = config
        self._candles: deque[Candle] = deque(maxlen=config.maxlen)

    @property
    def maxlen(self) -> int:
        return self._config.maxlen

    def __len__(self) -> int:
        return len(self._candles)

    def append(self, candle: Candle) -> None:
        self._candles.append(candle)

    def extend(self, candles: list[Candle]) -> None:
        for c in candles:
            self._candles.append(c)

    def snapshot(self) -> list[Candle]:
        return list(self._candles)

    def latest(self) -> Candle | None:
        if not self._candles:
            return None
        return self._candles[-1]
