from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.robustness import (
    run_candidate_validation,
    run_commission_stress_test,
    run_risk_sweep,
)
from src.backtest.walk_forward import make_wfa_folds_by_time
from src.data.normalizer import normalize_ohlcv_df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="reports/robustness/latest")
    parser.add_argument("--train-window", default="180D")
    parser.add_argument("--test-window", default="60D")
    parser.add_argument("--step-window", default="60D")
    args = parser.parse_args()

    df = normalize_ohlcv_df(pd.read_parquet(args.data))
    folds = make_wfa_folds_by_time(
        df,
        train_window=args.train_window,
        test_window=args.test_window,
        step_window=args.step_window,
    )

    out_dir = PROJECT_ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    candidate_results, candidate_summary = run_candidate_validation(folds)
    candidate_results.to_csv(out_dir / "candidate_validation.csv", index=False)
    candidate_summary.to_csv(out_dir / "candidate_summary.csv")

    risk_results, risk_summary = run_risk_sweep(folds)
    risk_results.to_csv(out_dir / "risk_sweep.csv", index=False)
    risk_summary.to_csv(out_dir / "risk_summary.csv")

    stress = run_commission_stress_test(df)
    stress.to_csv(out_dir / "commission_stress_test.csv", index=False)
    print(f"saved robustness reports to {out_dir}")


if __name__ == "__main__":
    main()
