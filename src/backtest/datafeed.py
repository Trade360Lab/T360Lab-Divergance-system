from __future__ import annotations

import backtrader as bt


class PandasTVData(bt.feeds.PandasData):
    lines = ("tv_rsi",)
    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
        ("openinterest", None),
        ("tv_rsi", "tv_rsi"),
    )
