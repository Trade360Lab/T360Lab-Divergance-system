import numpy as np
import pandas as pd

from src.backtest.runner import run_backtest
from src.strategy.params import StrategyParams


def synthetic_ohlcv(n: int = 220) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=n, freq="15min")
    base = 100 + np.sin(np.arange(n) / 6) * 3 + np.linspace(0, 2, n)
    open_ = base + np.sin(np.arange(n) / 3) * 0.2
    close = base + np.cos(np.arange(n) / 4) * 0.2
    high = np.maximum(open_, close) + 0.8
    low = np.minimum(open_, close) - 0.8
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


def test_run_backtest_returns_metrics_trades_and_equity_frames():
    params = StrategyParams(rsi_len=5, left_bars=2, right_bars=2, max_setup_bars=30)
    metrics, trades_df, equity_df = run_backtest(synthetic_ohlcv(), params=params)

    assert isinstance(trades_df, pd.DataFrame)
    assert isinstance(equity_df, pd.DataFrame)
    for key in [
        "net_pnl",
        "net_pnl_pct",
        "max_drawdown_pct",
        "total_trades",
        "winrate_pct",
        "profit_factor",
    ]:
        assert key in metrics
