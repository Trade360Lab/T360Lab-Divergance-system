from __future__ import annotations

import pandas as pd

from src.data.normalizer import normalize_ohlcv_df


REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def find_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    raw = df.copy().rename(columns={c: str(c).lower() for c in df.columns})
    if isinstance(raw.index, pd.DatetimeIndex):
        index = raw.index
    else:
        datetime_candidates = ["datetime", "date", "time", "timestamp", "open_time"]
        found = next((c for c in datetime_candidates if c in raw.columns), None)
        if found is None:
            return pd.DataFrame()
        if found == "open_time" and pd.api.types.is_numeric_dtype(raw[found]):
            index = pd.to_datetime(raw[found], unit="ms", utc=True, errors="coerce")
        else:
            index = pd.to_datetime(raw[found], utc=True, errors="coerce")
    return raw[index.duplicated(keep=False)]


def find_missing_bars(df: pd.DataFrame, freq: str = "15min") -> pd.DatetimeIndex:
    normalized = normalize_ohlcv_df(df)
    if normalized.empty:
        return pd.DatetimeIndex([])
    expected = pd.date_range(normalized.index.min(), normalized.index.max(), freq=freq)
    return expected.difference(normalized.index)


def validate_ohlcv_df(df: pd.DataFrame, freq: str = "15min") -> None:
    duplicates = find_duplicates(df)
    if not duplicates.empty:
        raise ValueError("OHLCV index contains duplicates")

    normalized = normalize_ohlcv_df(df)
    missing_cols = [c for c in REQUIRED_OHLCV_COLUMNS if c not in normalized.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    if not normalized.index.is_monotonic_increasing:
        raise ValueError("OHLCV index must be sorted")
    gaps = find_missing_bars(normalized, freq=freq)
    if len(gaps):
        raise ValueError(f"OHLCV data has missing bars: {len(gaps)}")

    invalid = (
        (normalized["high"] < normalized["low"])
        | (normalized["high"] < normalized["open"])
        | (normalized["high"] < normalized["close"])
        | (normalized["low"] > normalized["open"])
        | (normalized["low"] > normalized["close"])
    )
    if bool(invalid.any()):
        raise ValueError("OHLC sanity check failed")
