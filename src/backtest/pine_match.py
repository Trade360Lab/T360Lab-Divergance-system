from __future__ import annotations

from typing import Any

import pandas as pd

from src.backtest.runner import run_backtest
from src.data.normalizer import normalize_ohlcv_df
from src.strategy.params import StrategyParams


def run_pine_match_check(
    df: pd.DataFrame,
    params: StrategyParams | None = None,
    start: str = "2026-03-01",
    end: str = "2026-05-11",
    expected_trades: int = 39,
    expected_net_pnl_pct: float = 74.0,
    trades_tolerance: int = 1,
    net_pnl_pct_tolerance: float = 5.0,
    **backtest_kwargs: Any,
) -> dict[str, Any]:
    params = params or StrategyParams(
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
    normalized = normalize_ohlcv_df(df)
    sample = normalized.loc[(normalized.index >= pd.Timestamp(start)) & (normalized.index <= pd.Timestamp(end))]
    metrics, trades_df, equity_df = run_backtest(sample, params=params, **backtest_kwargs)
    trades_ok = abs(metrics["total_trades"] - expected_trades) <= trades_tolerance
    pnl_ok = abs(metrics["net_pnl_pct"] - expected_net_pnl_pct) <= net_pnl_pct_tolerance
    return {
        "ok": bool(trades_ok and pnl_ok),
        "metrics": metrics,
        "trades_df": trades_df,
        "equity_df": equity_df,
        "expected_trades": expected_trades,
        "expected_net_pnl_pct": expected_net_pnl_pct,
        "trades_tolerance": trades_tolerance,
        "net_pnl_pct_tolerance": net_pnl_pct_tolerance,
    }
