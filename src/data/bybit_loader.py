from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests


BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"


def _to_utc_ms(value: Any) -> int:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int(ts.timestamp() * 1000)


def load_bybit_klines(
    category: str = "spot",
    symbol: str = "BTCUSDT",
    interval: str = "15",
    start_time: Any = "2026-03-01 00:00:00",
    end_time: Any = "2026-05-11 00:00:00",
    limit: int = 1000,
    pause: float = 0.2,
    max_pages: int = 1000,
    retries: int = 3,
    backoff: float = 1.0,
    timeout: float = 30.0,
) -> pd.DataFrame:
    """
    Load raw Bybit OHLCV rows from /v5/market/kline.

    Bybit returns candles newest-to-oldest, so pagination moves backward with
    current_end, matching the notebook implementation.
    """
    start_ts = _to_utc_ms(start_time)
    end_ts = _to_utc_ms(end_time)

    if end_ts <= start_ts:
        raise ValueError("end_time must be later than start_time")
    if not 1 <= int(limit) <= 1000:
        raise ValueError("limit must be between 1 and 1000")

    all_rows = []
    current_end = end_ts
    session = requests.Session()

    for _page in range(max_pages):
        params = {
            "category": category,
            "symbol": symbol,
            "interval": str(interval),
            "start": start_ts,
            "end": current_end,
            "limit": int(limit),
        }

        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = session.get(BYBIT_KLINE_URL, params=params, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                break
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt + 1 >= retries:
                    raise RuntimeError(f"Bybit request failed after {retries} attempts") from last_error
                time.sleep(backoff * (2**attempt))

        if data.get("retCode") != 0:
            raise RuntimeError(f"Bybit API error: {data}")

        rows = data.get("result", {}).get("list", [])
        if not rows:
            break

        rows_sorted = sorted(rows, key=lambda x: int(x[0]))
        all_rows.extend(rows_sorted)

        oldest_start_time = int(rows_sorted[0][0])
        if oldest_start_time <= start_ts:
            break

        new_current_end = oldest_start_time - 1
        if new_current_end >= current_end:
            raise RuntimeError(
                f"Pagination stuck: current_end={current_end}, "
                f"new_current_end={new_current_end}"
            )

        current_end = new_current_end
        time.sleep(pause)
    else:
        raise RuntimeError(f"Reached max_pages={max_pages}. Possible pagination issue.")

    df = pd.DataFrame(
        all_rows,
        columns=["open_time", "open", "high", "low", "close", "volume", "turnover"],
    )

    if df.empty:
        return df

    df["open_time"] = df["open_time"].astype("int64")
    df["datetime"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.sort_values("datetime").drop_duplicates(subset=["open_time"]).reset_index(drop=True)

    start_dt = pd.Timestamp(start_time)
    end_dt = pd.Timestamp(end_time)
    if start_dt.tzinfo is not None:
        start_dt = start_dt.tz_convert(None)
    if end_dt.tzinfo is not None:
        end_dt = end_dt.tz_convert(None)

    return df[(df["datetime"] >= start_dt) & (df["datetime"] <= end_dt)].reset_index(drop=True)
