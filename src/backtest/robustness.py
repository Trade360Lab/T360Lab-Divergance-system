from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.runner import run_backtest
from src.strategy.params import BASELINE_PARAMS, StrategyParams


def _summary_by(grouped: pd.core.groupby.DataFrameGroupBy) -> pd.DataFrame:
    return grouped.agg(
        folds=("fold", "count"),
        positive_folds=("net_pnl_pct", lambda x: (x > 0).sum()),
        positive_folds_pct=("net_pnl_pct", lambda x: (x > 0).mean() * 100),
        avg_pnl_pct=("net_pnl_pct", "mean"),
        median_pnl_pct=("net_pnl_pct", "median"),
        avg_pf=("profit_factor", lambda x: x.replace([np.inf, -np.inf], np.nan).mean()),
        median_pf=("profit_factor", lambda x: x.replace([np.inf, -np.inf], np.nan).median()),
        max_dd_pct=("max_drawdown_pct", "max"),
        avg_dd_pct=("max_drawdown_pct", "mean"),
        total_trades=("total_trades", "sum"),
    )


def default_candidate_params(base: StrategyParams = BASELINE_PARAMS) -> dict[str, StrategyParams]:
    return {
        "baseline_13_3_5_15_buf0_mb100": replace(
            base,
            rsi_len=13,
            left_bars=3,
            right_bars=5,
            rr=1.5,
            stop_buffer_pct=0.0,
            max_setup_bars=100,
        ),
        "baseline_13_3_5_15_buf0_mb90": replace(
            base,
            rsi_len=13,
            left_bars=3,
            right_bars=5,
            rr=1.5,
            stop_buffer_pct=0.0,
            max_setup_bars=90,
        ),
        "conservative_11_4_5_15_buf005_mb90": replace(
            base,
            rsi_len=11,
            left_bars=4,
            right_bars=5,
            rr=1.5,
            stop_buffer_pct=0.05,
            max_setup_bars=90,
        ),
        "conservative_12_4_5_15_buf005_mb90": replace(
            base,
            rsi_len=12,
            left_bars=4,
            right_bars=5,
            rr=1.5,
            stop_buffer_pct=0.05,
            max_setup_bars=90,
        ),
        "slower_13_4_5_15_buf0_mb100": replace(
            base,
            rsi_len=13,
            left_bars=4,
            right_bars=5,
            rr=1.5,
            stop_buffer_pct=0.0,
            max_setup_bars=100,
        ),
    }


def run_candidate_validation(
    folds: list[dict[str, Any]],
    candidates: dict[str, StrategyParams] | None = None,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = candidates or default_candidate_params()
    rows = []
    for name, params in candidates.items():
        for fold_id, fold in enumerate(folds):
            metrics, _, _ = run_backtest(
                fold["test_df"],
                params,
                start_cash=start_cash,
                commission=commission,
                broker_leverage=broker_leverage,
            )
            rows.append(
                {
                    "candidate": name,
                    "fold": fold_id,
                    "test_start": fold["test_start"],
                    "test_end": fold["test_end"],
                    **metrics,
                }
            )
    results = pd.DataFrame(rows)
    return results, _summary_by(results.groupby("candidate"))


def run_risk_sweep(
    folds: list[dict[str, Any]] | None,
    df: pd.DataFrame | None = None,
    base: StrategyParams = BASELINE_PARAMS,
    risk_values: list[float] | None = None,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    risk_values = risk_values or [0.5, 1.0, 1.5, 2.0, 3.0]
    rows = []
    if folds is not None:
        for risk in risk_values:
            params = replace(base, risk_pct=risk)
            for fold_id, fold in enumerate(folds):
                metrics, _, _ = run_backtest(
                    fold["test_df"],
                    params,
                    start_cash=start_cash,
                    commission=commission,
                    broker_leverage=broker_leverage,
                )
                rows.append(
                    {
                        "risk_pct": risk,
                        "fold": fold_id,
                        "test_start": fold["test_start"],
                        "test_end": fold["test_end"],
                        **metrics,
                    }
                )
        results = pd.DataFrame(rows)
        return results, _summary_by(results.groupby("risk_pct"))

    if df is None:
        raise ValueError("df is required when folds is None")

    for risk in risk_values:
        metrics, _, _ = run_backtest(
            df,
            replace(base, risk_pct=risk),
            start_cash=start_cash,
            commission=commission,
            broker_leverage=broker_leverage,
        )
        rows.append({"risk_pct": risk, **metrics})
    results = pd.DataFrame(rows)
    return results, results


def run_commission_stress_test(
    df: pd.DataFrame,
    base: StrategyParams = BASELINE_PARAMS,
    commissions: list[float] | None = None,
    risk_values: list[float] | None = None,
    start_cash: float = 10_000.0,
    broker_leverage: float = 100.0,
) -> pd.DataFrame:
    commissions = commissions or [0.0004, 0.0006, 0.0008, 0.0010]
    risk_values = risk_values or [1.0, 2.0]
    rows = []
    for commission in commissions:
        for risk in risk_values:
            metrics, _, _ = run_backtest(
                df,
                replace(base, risk_pct=risk),
                start_cash=start_cash,
                commission=commission,
                broker_leverage=broker_leverage,
            )
            rows.append({"risk_pct": risk, "commission": commission, **metrics})
    return pd.DataFrame(rows)
