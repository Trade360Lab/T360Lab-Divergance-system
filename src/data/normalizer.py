from __future__ import annotations

import pandas as pd


def normalize_ohlcv_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OHLCV data to the Backtrader-compatible notebook format.

    Result:
        index: timezone-naive DatetimeIndex
        columns: open, high, low, close, volume
    """
    df = df.copy()
    df = df.rename(columns={c: str(c).lower() for c in df.columns})

    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "volume" not in df.columns:
        df["volume"] = 0.0

    if not isinstance(df.index, pd.DatetimeIndex):
        datetime_candidates = ["datetime", "date", "time", "timestamp", "open_time"]
        found = next((c for c in datetime_candidates if c in df.columns), None)
        if found is None:
            raise ValueError("Need DatetimeIndex or datetime/date/time/timestamp/open_time column")

        if found == "open_time" and pd.api.types.is_numeric_dtype(df[found]):
            df[found] = pd.to_datetime(df[found], unit="ms", utc=True, errors="coerce")
        else:
            df[found] = pd.to_datetime(df[found], utc=True, errors="coerce")
        df = df.set_index(found)

    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"])
    return df[numeric_cols]
