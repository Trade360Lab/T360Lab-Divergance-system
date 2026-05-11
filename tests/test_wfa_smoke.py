import numpy as np
import pandas as pd
import pytest

from src.backtest.walk_forward import make_wfa_folds_by_bars, run_walk_forward
from src.strategy.params import StrategyParams


def synthetic_ohlcv(n: int = 220) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=n, freq="15min")
    base = 100 + np.sin(np.arange(n) / 5) * 4
    open_ = base + np.sin(np.arange(n) / 2) * 0.3
    close = base + np.cos(np.arange(n) / 3) * 0.3
    high = np.maximum(open_, close) + 1.0
    low = np.minimum(open_, close) - 1.0
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.ones(n),
        },
        index=index,
    )


@pytest.mark.slow
def test_walk_forward_smoke_with_tiny_optuna_budget():
    df = synthetic_ohlcv()
    folds = make_wfa_folds_by_bars(df, train_bars=90, test_bars=40, step_bars=40)
    assert folds

    result = run_walk_forward(
        folds[:1],
        base=StrategyParams(rsi_len=5, left_bars=2, right_bars=2, max_setup_bars=30),
        n_trials_per_fold=2,
        min_trades=1,
    )

    assert len(result) == 1
    assert "train_net_pnl_pct" in result.columns
    assert "test_net_pnl_pct" in result.columns
