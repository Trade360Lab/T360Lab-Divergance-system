from __future__ import annotations

import numpy as np
import pandas as pd


def tv_rma(series: pd.Series, length: int) -> pd.Series:
    """
    PineScript ta.rma equivalent from the notebook.

    The first value is SMA over the first length valid observations; next
    values use alpha * x + (1 - alpha) * prev, alpha = 1 / length.
    """
    if length <= 0:
        raise ValueError("length must be > 0")

    x = pd.Series(series, dtype="float64").copy()
    out = pd.Series(np.nan, index=x.index, dtype="float64")
    alpha = 1.0 / length

    valid = x.dropna()
    if len(valid) < length:
        return out

    first_idx = valid.index[length - 1]
    first_value = valid.iloc[:length].mean()
    out.loc[first_idx] = first_value

    prev = first_value
    started = False
    for idx, value in x.items():
        if idx == first_idx:
            started = True
            continue
        if not started:
            continue
        if np.isnan(value):
            out.loc[idx] = prev
            continue
        prev = alpha * value + (1.0 - alpha) * prev
        out.loc[idx] = prev

    return out


def tv_rsi(close: pd.Series, length: int) -> pd.Series:
    """PineScript ta.rsi(close, length) approximation with Wilder RMA."""
    close = pd.Series(close, dtype="float64")
    change = close.diff()
    up = change.clip(lower=0)
    down = (-change).clip(lower=0)

    rma_up = tv_rma(up, length)
    rma_down = tv_rma(down, length)

    rs = rma_up / rma_down
    rsi = 100.0 - (100.0 / (1.0 + rs))

    rsi = rsi.where(rma_down != 0, 100.0)
    rsi = rsi.where(rma_up != 0, 0.0)
    rsi = rsi.where(~((rma_up == 0) & (rma_down == 0)), 50.0)

    return rsi
