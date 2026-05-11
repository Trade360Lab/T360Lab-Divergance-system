from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

try:
    import optuna
except ImportError:
    optuna = None

from src.backtest.runner import run_backtest
from src.strategy.params import BASELINE_PARAMS, StrategyParams


def trial_to_params(
    trial: "optuna.Trial",
    base: StrategyParams = BASELINE_PARAMS,
) -> StrategyParams:
    """Optimization range around the current notebook baseline. Risk is not optimized."""
    return StrategyParams(
        rsi_len=trial.suggest_int("rsi_len", 11, 15),
        left_bars=trial.suggest_int("left_bars", 2, 4),
        right_bars=trial.suggest_int("right_bars", 4, 6),
        rr=trial.suggest_categorical("rr", [1.25, 1.5, 1.75, 2.0]),
        risk_pct=base.risk_pct,
        stop_buffer_pct=trial.suggest_categorical("stop_buffer_pct", [0.0, 0.05]),
        stop_mode=base.stop_mode,
        max_setup_bars=trial.suggest_int("max_setup_bars", 70, 110, step=10),
        strict_pivots=base.strict_pivots,
    )


def make_objective(
    train_df: pd.DataFrame,
    base: StrategyParams = BASELINE_PARAMS,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
    min_trades: int = 50,
    max_dd_pct: float = 30.0,
):
    """Notebook objective: PF plus soft PnL bonus, with low-trade/loss/DD penalties."""
    if optuna is None:
        raise ImportError("Optuna is not installed: pip install optuna")

    def objective(trial: "optuna.Trial") -> float:
        params = trial_to_params(trial, base=base)

        metrics, _, _ = run_backtest(
            train_df,
            params=params,
            start_cash=start_cash,
            commission=commission,
            broker_leverage=broker_leverage,
        )

        pf = metrics.get("profit_factor", 0.0)
        net_pnl_pct = metrics.get("net_pnl_pct", 0.0)
        dd_pct = metrics.get("max_drawdown_pct", 0.0)
        trades = metrics.get("total_trades", 0)

        if not np.isfinite(pf):
            pf = 10.0

        score = float(pf)

        if np.isfinite(net_pnl_pct):
            score += net_pnl_pct * 0.01

        if trades < min_trades:
            score *= max(trades, 1) / min_trades

        if net_pnl_pct <= 0:
            score *= 0.1

        if np.isfinite(dd_pct) and dd_pct > max_dd_pct:
            score *= max_dd_pct / dd_pct

        for key, value in metrics.items():
            if isinstance(value, (int, float, np.integer, np.floating)) and np.isfinite(value):
                trial.set_user_attr(key, float(value))

        return float(score)

    return objective


def optimize_params(
    train_df: pd.DataFrame,
    base: StrategyParams = BASELINE_PARAMS,
    n_trials: int = 300,
    sampler_seed: int = 42,
    direction: str = "maximize",
) -> "optuna.Study":
    if optuna is None:
        raise ImportError("Optuna is not installed: pip install optuna")

    sampler = optuna.samplers.TPESampler(seed=sampler_seed)
    study = optuna.create_study(direction=direction, sampler=sampler)
    study.optimize(make_objective(train_df, base=base), n_trials=n_trials, show_progress_bar=True)
    return study


def study_results_frame(study: "optuna.Study") -> pd.DataFrame:
    rows = []
    for trial in study.trials:
        row = dict(number=trial.number, value=trial.value, state=str(trial.state))
        row.update(trial.params)
        row.update(trial.user_attrs)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("value", ascending=False)


def params_from_trial_params(
    trial_params: dict[str, Any],
    base: StrategyParams = BASELINE_PARAMS,
) -> StrategyParams:
    """Convert best_trial.params back to StrategyParams."""
    return StrategyParams(
        rsi_len=int(trial_params.get("rsi_len", base.rsi_len)),
        left_bars=int(trial_params.get("left_bars", base.left_bars)),
        right_bars=int(trial_params.get("right_bars", base.right_bars)),
        rr=float(trial_params.get("rr", base.rr)),
        risk_pct=float(base.risk_pct),
        stop_buffer_pct=float(trial_params.get("stop_buffer_pct", base.stop_buffer_pct)),
        stop_mode=base.stop_mode,
        max_setup_bars=int(trial_params.get("max_setup_bars", base.max_setup_bars)),
        strict_pivots=base.strict_pivots,
    )


def evaluate_train_test(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    params: StrategyParams,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
) -> pd.DataFrame:
    train_metrics, _, _ = run_backtest(train_df, params, start_cash, commission, broker_leverage)
    test_metrics, _, _ = run_backtest(test_df, params, start_cash, commission, broker_leverage)
    return pd.DataFrame([train_metrics, test_metrics], index=["train", "test"])


if optuna is not None:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
