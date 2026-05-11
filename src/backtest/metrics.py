from __future__ import annotations

from typing import Any

import pandas as pd


def _max_drawdown_pct(equity: pd.Series) -> float:
    if equity.empty:
        return float("nan")
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    return abs(float(dd.min())) * 100.0


def _trade_metrics(trades: pd.DataFrame, prefix: str = "") -> dict[str, Any]:
    if trades.empty:
        return {
            f"{prefix}total_trades": 0,
            f"{prefix}winning_trades": 0,
            f"{prefix}losing_trades": 0,
            f"{prefix}winrate_pct": 0.0,
            f"{prefix}gross_profit": 0.0,
            f"{prefix}gross_loss": 0.0,
            f"{prefix}profit_factor": 0.0,
            f"{prefix}avg_pnl": 0.0,
            f"{prefix}avg_win": 0.0,
            f"{prefix}avg_loss": 0.0,
        }

    pnl = trades["pnlcomm"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    pf = float("inf") if gross_loss == 0 and gross_profit > 0 else (
        gross_profit / gross_loss if gross_loss > 0 else 0.0
    )

    return {
        f"{prefix}total_trades": int(len(trades)),
        f"{prefix}winning_trades": int((pnl > 0).sum()),
        f"{prefix}losing_trades": int((pnl < 0).sum()),
        f"{prefix}winrate_pct": float((pnl > 0).mean() * 100.0),
        f"{prefix}gross_profit": gross_profit,
        f"{prefix}gross_loss": gross_loss,
        f"{prefix}profit_factor": pf,
        f"{prefix}avg_pnl": float(pnl.mean()),
        f"{prefix}avg_win": float(wins.mean()) if len(wins) else 0.0,
        f"{prefix}avg_loss": float(losses.mean()) if len(losses) else 0.0,
    }


def compute_metrics(
    equity_curve: list[dict[str, Any]] | pd.DataFrame,
    trade_records: list[dict[str, Any]] | pd.DataFrame,
    start_cash: float,
) -> dict[str, Any]:
    eq = equity_curve.copy() if isinstance(equity_curve, pd.DataFrame) else pd.DataFrame(equity_curve)
    trades = (
        trade_records.copy() if isinstance(trade_records, pd.DataFrame) else pd.DataFrame(trade_records)
    )

    if eq.empty:
        final_equity = start_cash
        max_dd = float("nan")
    else:
        if "dt" in eq.columns:
            eq = eq.set_index("dt")
        final_equity = float(eq["equity"].iloc[-1])
        max_dd = _max_drawdown_pct(eq["equity"])

    metrics: dict[str, Any] = {
        "start_cash": float(start_cash),
        "final_equity": final_equity,
        "net_pnl": final_equity - float(start_cash),
        "net_pnl_pct": (final_equity / float(start_cash) - 1.0) * 100.0,
        "max_drawdown_pct": max_dd,
    }

    metrics.update(_trade_metrics(trades, prefix=""))

    if not trades.empty and "side" in trades.columns:
        metrics.update(_trade_metrics(trades[trades["side"] == "long"], prefix="long_"))
        metrics.update(_trade_metrics(trades[trades["side"] == "short"], prefix="short_"))
    else:
        metrics.update(_trade_metrics(pd.DataFrame(), prefix="long_"))
        metrics.update(_trade_metrics(pd.DataFrame(), prefix="short_"))

    return metrics


def metrics_to_frame(metrics_list: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(metrics_list)
