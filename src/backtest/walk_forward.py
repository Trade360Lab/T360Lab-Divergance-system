from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd

try:
    import optuna
except ImportError:
    optuna = None

from src.backtest.optuna_runner import make_objective, params_from_trial_params
from src.backtest.runner import run_backtest
from src.data.normalizer import normalize_ohlcv_df
from src.strategy.params import BASELINE_PARAMS, StrategyParams


def make_wfa_folds_by_bars(
    df: pd.DataFrame,
    train_bars: int,
    test_bars: int,
    step_bars: int | None = None,
    expanding: bool = False,
) -> list[dict[str, Any]]:
    df = normalize_ohlcv_df(df)
    step_bars = step_bars or test_bars
    folds = []
    start = 0

    while True:
        train_start = 0 if expanding else start
        train_end = start + train_bars
        test_start = train_end
        test_end = test_start + test_bars

        if test_end > len(df):
            break

        folds.append(
            dict(
                train_start=df.index[train_start],
                train_end=df.index[train_end - 1],
                test_start=df.index[test_start],
                test_end=df.index[test_end - 1],
                train_df=df.iloc[train_start:train_end].copy(),
                test_df=df.iloc[test_start:test_end].copy(),
            )
        )
        start += step_bars

    return folds


def make_wfa_folds_by_time(
    df: pd.DataFrame,
    train_window: str | pd.Timedelta,
    test_window: str | pd.Timedelta,
    step_window: str | pd.Timedelta | None = None,
    expanding: bool = False,
) -> list[dict[str, Any]]:
    df = normalize_ohlcv_df(df)
    train_delta = pd.Timedelta(train_window)
    test_delta = pd.Timedelta(test_window)
    step_delta = pd.Timedelta(step_window) if step_window is not None else test_delta

    folds = []
    first = df.index.min()
    last = df.index.max()
    anchor = first

    while True:
        train_start = first if expanding else anchor
        train_end = anchor + train_delta
        test_start = train_end
        test_end = test_start + test_delta

        if test_end > last:
            break

        train_df = df[(df.index >= train_start) & (df.index < train_end)].copy()
        test_df = df[(df.index >= test_start) & (df.index < test_end)].copy()

        if len(train_df) > 0 and len(test_df) > 0:
            folds.append(
                dict(
                    train_start=train_df.index.min(),
                    train_end=train_df.index.max(),
                    test_start=test_df.index.min(),
                    test_end=test_df.index.max(),
                    train_df=train_df,
                    test_df=test_df,
                )
            )

        anchor = anchor + step_delta

    return folds


def run_walk_forward(
    folds: list[dict[str, Any]],
    base: StrategyParams = BASELINE_PARAMS,
    n_trials_per_fold: int = 150,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
    sampler_seed: int = 42,
    min_trades: int = 50,
    max_dd_pct: float = 30.0,
) -> pd.DataFrame:
    if optuna is None:
        raise ImportError("Optuna is not installed: pip install optuna")

    rows = []
    for fold_id, fold in enumerate(folds):
        sampler = optuna.samplers.TPESampler(seed=sampler_seed + fold_id)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        objective = make_objective(
            fold["train_df"],
            base=base,
            start_cash=start_cash,
            commission=commission,
            broker_leverage=broker_leverage,
            min_trades=min_trades,
            max_dd_pct=max_dd_pct,
        )
        study.optimize(
            objective,
            n_trials=n_trials_per_fold,
            show_progress_bar=False,
            gc_after_trial=True,
        )

        best_params = params_from_trial_params(study.best_trial.params, base=base)
        train_metrics, _, _ = run_backtest(
            fold["train_df"],
            best_params,
            start_cash=start_cash,
            commission=commission,
            broker_leverage=broker_leverage,
        )
        test_metrics, _, _ = run_backtest(
            fold["test_df"],
            best_params,
            start_cash=start_cash,
            commission=commission,
            broker_leverage=broker_leverage,
        )

        row = {
            "fold": fold_id,
            "train_start": fold["train_start"],
            "train_end": fold["train_end"],
            "test_start": fold["test_start"],
            "test_end": fold["test_end"],
            "study_best_value": study.best_value,
            "study_best_trial": study.best_trial.number,
            **{f"param_{k}": v for k, v in asdict(best_params).items()},
            **{f"train_{k}": v for k, v in train_metrics.items()},
            **{f"test_{k}": v for k, v in test_metrics.items()},
        }
        rows.append(row)

    return pd.DataFrame(rows)
