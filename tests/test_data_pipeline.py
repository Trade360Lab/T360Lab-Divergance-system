import pandas as pd
import pytest

from src.data.normalizer import normalize_ohlcv_df
from src.data.validators import find_duplicates, find_missing_bars, validate_ohlcv_df


def test_normalize_ohlcv_sorts_deduplicates_and_handles_timezone():
    raw = pd.DataFrame(
        {
            "datetime": [
                "2024-01-01 00:15:00+00:00",
                "2024-01-01 00:00:00+00:00",
                "2024-01-01 00:15:00+00:00",
            ],
            "open": ["101", "100", "102"],
            "high": ["103", "102", "104"],
            "low": ["100", "99", "101"],
            "close": ["102", "101", "103"],
            "volume": ["1.0", "2.0", "3.0"],
        }
    )

    normalized = normalize_ohlcv_df(raw)

    assert list(normalized.columns) == ["open", "high", "low", "close", "volume"]
    assert normalized.index.is_monotonic_increasing
    assert normalized.index.tz is None
    assert len(normalized) == 2
    assert normalized.iloc[-1]["open"] == 102.0


def test_validators_detect_duplicates_gaps_and_ohlc_sanity():
    raw = pd.DataFrame(
        {
            "datetime": [
                "2024-01-01 00:00:00",
                "2024-01-01 00:15:00",
                "2024-01-01 00:15:00",
                "2024-01-01 00:45:00",
            ],
            "open": [100, 101, 101, 103],
            "high": [102, 103, 103, 104],
            "low": [99, 100, 100, 102],
            "close": [101, 102, 102, 103],
            "volume": [1, 1, 1, 1],
        }
    )

    assert len(find_duplicates(raw)) == 2
    with pytest.raises(ValueError, match="duplicates"):
        validate_ohlcv_df(raw)

    normalized = normalize_ohlcv_df(raw)
    missing = find_missing_bars(normalized, freq="15min")
    assert pd.Timestamp("2024-01-01 00:30:00") in missing

    continuous = normalized.reindex(pd.date_range(normalized.index.min(), normalized.index.max(), freq="15min"))
    continuous = continuous.ffill()
    invalid = continuous.copy()
    invalid.loc[invalid.index[0], "high"] = invalid.loc[invalid.index[0], "low"] - 1
    with pytest.raises(ValueError, match="sanity"):
        validate_ohlcv_df(invalid, freq="15min")
