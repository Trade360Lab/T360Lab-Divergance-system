from __future__ import annotations

from dataclasses import asdict
from typing import Any

import backtrader as bt
import pandas as pd

from src.backtest.datafeed import PandasTVData
from src.backtest.div_breakout_bt import DivBreakoutRiskStrategy
from src.backtest.metrics import compute_metrics
from src.data.normalizer import normalize_ohlcv_df
from src.indicators.tv_rsi import tv_rsi
from src.strategy.params import BASELINE_PARAMS, StrategyParams


def prepare_backtrader_df(df: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    """Add tv_rsi and clean data before Backtrader."""
    params.validate()
    out = normalize_ohlcv_df(df)
    out["tv_rsi"] = tv_rsi(out["close"], params.rsi_len)
    return out.dropna(subset=["tv_rsi"])


def _strategy_frames(
    strat: DivBreakoutRiskStrategy,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trades_df = pd.DataFrame(strat.trade_records)
    equity_df = pd.DataFrame(strat.equity_curve)
    events_df = pd.DataFrame(strat.event_log)

    if not equity_df.empty and "dt" in equity_df.columns:
        equity_df = equity_df.set_index("dt")
    return trades_df, equity_df, events_df


def run_backtest_details(
    df: pd.DataFrame,
    params: StrategyParams = BASELINE_PARAMS,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
    cheat_on_close: bool = True,
    printlog: bool = False,
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    DivBreakoutRiskStrategy,
    bt.Cerebro,
]:
    """
    Main runner with full internals.

    commission=0.0004 matches Pine commission_value=0.04. High broker_leverage
    is preserved from the notebook to avoid Backtrader cash-limit rejections.
    """
    params.validate()
    bt_df = prepare_backtrader_df(df, params)

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(start_cash)
    cerebro.broker.setcommission(commission=commission, leverage=broker_leverage)
    cerebro.broker.set_coc(cheat_on_close)

    data = PandasTVData(dataname=bt_df)
    cerebro.adddata(data)

    kwargs = asdict(params)
    kwargs["printlog"] = printlog
    cerebro.addstrategy(DivBreakoutRiskStrategy, **kwargs)

    results = cerebro.run(tradehistory=False)
    strat = results[0]
    trades_df, equity_df, events_df = _strategy_frames(strat)
    metrics = compute_metrics(equity_df, trades_df, start_cash=start_cash)
    return metrics, trades_df, equity_df, events_df, strat, cerebro


def run_backtest(
    df: pd.DataFrame,
    params: StrategyParams = BASELINE_PARAMS,
    start_cash: float = 10_000.0,
    commission: float = 0.0004,
    broker_leverage: float = 100.0,
    cheat_on_close: bool = True,
    printlog: bool = False,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    metrics, trades_df, equity_df, _events_df, _strat, _cerebro = run_backtest_details(
        df=df,
        params=params,
        start_cash=start_cash,
        commission=commission,
        broker_leverage=broker_leverage,
        cheat_on_close=cheat_on_close,
        printlog=printlog,
    )
    return metrics, trades_df, equity_df
