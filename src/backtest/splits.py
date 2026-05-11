from __future__ import annotations

import pandas as pd

from src.data.normalizer import normalize_ohlcv_df


def split_train_test_by_ratio(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < train_ratio < 1:
        raise ValueError("train_ratio must be between 0 and 1")
    df = normalize_ohlcv_df(df)
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def split_train_test_by_date(
    df: pd.DataFrame,
    split_date: str | pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = normalize_ohlcv_df(df)
    split_ts = pd.Timestamp(split_date)
    if df.index.tz is not None and split_ts.tzinfo is None:
        split_ts = split_ts.tz_localize(df.index.tz)
    train = df.loc[df.index < split_ts].copy()
    test = df.loc[df.index >= split_ts].copy()
    return train, test
