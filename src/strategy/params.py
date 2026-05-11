from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyParams:
    rsi_len: int = 13
    left_bars: int = 3
    right_bars: int = 5
    rr: float = 1.5
    risk_pct: float = 3.0
    stop_buffer_pct: float = 0.0
    stop_mode: str = "Nearest pivot"
    max_setup_bars: int = 90
    strict_pivots: bool = False

    def validate(self) -> None:
        if self.rsi_len < 2:
            raise ValueError("rsi_len must be >= 2")
        if self.left_bars < 1 or self.right_bars < 1:
            raise ValueError("left_bars/right_bars must be >= 1")
        if self.rr <= 0:
            raise ValueError("rr must be > 0")
        if self.risk_pct <= 0:
            raise ValueError("risk_pct must be > 0")
        if self.stop_buffer_pct < 0:
            raise ValueError("stop_buffer_pct must be >= 0")
        if self.stop_mode not in {"Nearest pivot", "Deepest pivot"}:
            raise ValueError("stop_mode must be 'Nearest pivot' or 'Deepest pivot'")


BASELINE_PARAMS = StrategyParams()
