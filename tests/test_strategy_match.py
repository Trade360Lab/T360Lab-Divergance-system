from pathlib import Path

import pandas as pd
import pytest

from src.backtest.pine_match import run_pine_match_check
from src.strategy.params import StrategyParams


@pytest.mark.regression
def test_pine_match_regression_if_local_data_available():
    data_path = Path("data/processed/BTCUSDT_15.parquet")
    if not data_path.exists():
        pytest.skip("local BTCUSDT_15 parquet is not available")

    params = StrategyParams(
        rsi_len=13,
        left_bars=3,
        right_bars=5,
        rr=1.5,
        risk_pct=3.0,
        stop_buffer_pct=0.0,
        stop_mode="Nearest pivot",
        max_setup_bars=90,
        strict_pivots=False,
    )
    result = run_pine_match_check(pd.read_parquet(data_path), params=params)
    assert result["ok"], result["metrics"]
