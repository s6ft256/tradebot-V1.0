from __future__ import annotations

from typing import Protocol, TypeVar


TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class Agent(Protocol[TIn, TOut]):
    def run(self, data: TIn) -> TOut: ...
