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

from src.backtest.runner import run_backtest_details
from src.data.normalizer import normalize_ohlcv_df
from src.strategy.params import StrategyParams


def _json_default(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp,)):
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
    parser.add_argument("--backtest-config", default="config/backtest.yaml")
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="reports/backtests/latest")
    args = parser.parse_args()

    params = _load_strategy(args.strategy_config)
    with open(args.backtest_config, "r", encoding="utf-8") as handle:
        backtest = yaml.safe_load(handle)["backtest"]

    df = normalize_ohlcv_df(pd.read_parquet(args.data))
    metrics, trades_df, equity_df, events_df, _strat, _cerebro = run_backtest_details(
        df,
        params=params,
        start_cash=float(backtest["start_cash"]),
        commission=float(backtest["commission"]),
        broker_leverage=float(backtest["broker_leverage"]),
        cheat_on_close=bool(backtest["cheat_on_close"]),
    )

    out_dir = PROJECT_ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, default=_json_default)
    trades_df.to_csv(out_dir / "trades.csv", index=False)
    equity_df.to_csv(out_dir / "equity_curve.csv")
    if not events_df.empty:
        events_df.to_csv(out_dir / "events.csv", index=False)
    print(f"saved backtest report to {out_dir}")


if __name__ == "__main__":
    main()
