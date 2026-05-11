from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.normalizer import normalize_ohlcv_df


def load_ohlcv_cache(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    return normalize_ohlcv_df(pd.read_parquet(path))


def save_ohlcv_cache(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalize_ohlcv_df(df).to_parquet(path)


def update_ohlcv_cache(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if existing_df is not None and not existing_df.empty:
        frames.append(normalize_ohlcv_df(existing_df))
    if new_df is not None and not new_df.empty:
        frames.append(normalize_ohlcv_df(new_df))
    if not frames:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    out = pd.concat(frames).sort_index()
    return out[~out.index.duplicated(keep="last")]
