import numpy as np
import pandas as pd
import pytest

from src.indicators.tv_rsi import tv_rma, tv_rsi


def test_tv_rma_starts_with_sma_then_wilder_update():
    series = pd.Series([1.0, 2.0, 3.0, 4.0])
    result = tv_rma(series, 3)

    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx((1.0 / 3.0) * 4.0 + (2.0 / 3.0) * 2.0)


def test_tv_rsi_warmup_and_edge_cases():
    close = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0])
    result = tv_rsi(close, 3)

    assert result.iloc[:3].isna().all()
    assert result.iloc[3] == pytest.approx(50.0)
    assert result.iloc[4] == pytest.approx(50.0)


def test_tv_rsi_stable_synthetic_values():
    close = pd.Series([1.0, 2.0, 3.0, 2.0, 2.5, 3.5, 3.0])
    result = tv_rsi(close, 3)

    assert result.iloc[3] == pytest.approx(66.6666667)
    assert result.iloc[4] == pytest.approx(73.3333333)
    assert result.iloc[5] == pytest.approx(83.3333333)
    assert result.iloc[6] == pytest.approx(65.0406504)
