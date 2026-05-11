from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.walk_forward import make_wfa_folds_by_time, run_walk_forward
from src.data.normalizer import normalize_ohlcv_df
from src.strategy.params import StrategyParams


def _json_default(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
        return None
    return str(value)


def _load_strategy(path: str | Path) -> StrategyParams:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)["strategy"]
    allowed = {field.name for field in fields(StrategyParams)}
    return StrategyParams(**{key: value for key, value in data.items() if key in allowed})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy-config", default="config/strategy.yaml")
    parser.add_argument("--optimization-config", default="config/optimization.yaml")
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="reports/wfa/latest")
    args = parser.parse_args()

    params = _load_strategy(args.strategy_config)
    with open(args.optimization_config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    df = normalize_ohlcv_df(pd.read_parquet(args.data))
    folds = make_wfa_folds_by_time(
        df,
        train_window=config["wfa"]["train_window"],
        test_window=config["wfa"]["test_window"],
        step_window=config["wfa"]["step_window"],
        expanding=bool(config["wfa"]["expanding"]),
    )
    result = run_walk_forward(
        folds,
        base=params,
        n_trials_per_fold=int(config["optimization"]["n_trials"]),
        sampler_seed=int(config["optimization"]["sampler_seed"]),
        min_trades=int(config["optimization"]["min_trades"]),
        max_dd_pct=float(config["optimization"]["max_dd_pct"]),
    )

    out_dir = PROJECT_ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_dir / "folds.csv", index=False)
    summary = {
        "folds": int(len(result)),
        "positive_test_folds": int((result["test_net_pnl_pct"] > 0).sum()) if len(result) else 0,
        "avg_test_pnl_pct": float(result["test_net_pnl_pct"].mean()) if len(result) else 0.0,
        "median_test_pnl_pct": float(result["test_net_pnl_pct"].median()) if len(result) else 0.0,
        "total_test_trades": int(result["test_total_trades"].sum()) if len(result) else 0,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, default=_json_default)
    print(f"saved wfa report to {out_dir}")


if __name__ == "__main__":
    main()
