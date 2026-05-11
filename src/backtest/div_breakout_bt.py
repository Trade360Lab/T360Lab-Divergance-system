from __future__ import annotations

from typing import Any

import backtrader as bt
import numpy as np


class DivBreakoutRiskStrategy(bt.Strategy):
    params = dict(
        rsi_len=13,
        left_bars=3,
        right_bars=5,
        rr=1.5,
        risk_pct=3.0,
        stop_buffer_pct=0.0,
        stop_mode="Nearest pivot",
        max_setup_bars=90,
        strict_pivots=False,
        printlog=False,
    )

    def __init__(self):
        self.prev_price_low = None
        self.prev_rsi_low = None
        self.prev_low_high = None
        self.prev_low_index = None

        self.prev_price_high = None
        self.prev_rsi_high = None
        self.prev_high_low = None
        self.prev_high_index = None

        self.bull_active = False
        self.bull_trigger = None
        self.bull_stop = None
        self.bull_take = None
        self.bull_setup_bar = None

        self.bear_active = False
        self.bear_trigger = None
        self.bear_stop = None
        self.bear_take = None
        self.bear_setup_bar = None

        self.entry_order = None
        self.stop_order = None
        self.limit_order = None
        self.entry_meta: dict[int, dict[str, Any]] = {}

        self.equity_curve: list[dict[str, Any]] = []
        self.trade_records: list[dict[str, Any]] = []
        self.event_log: list[dict[str, Any]] = []
        self.current_trade_side: str | None = None
        self.current_trade_entry_dt = None
        self.current_trade_entry_bar = None
        self.current_trade_entry_price = None

    def log(self, txt: str) -> None:
        if self.p.printlog:
            dt = self.data.datetime.datetime(0)
            print(f"{dt.isoformat()} {txt}")

    @property
    def bar_index(self) -> int:
        return len(self.data) - 1

    def _enough_for_pivot(self) -> bool:
        return len(self.data) >= (self.p.left_bars + self.p.right_bars + 1)

    def _is_pivot_low_now(self) -> bool:
        rb = self.p.right_bars
        lb = self.p.left_bars
        pivot = float(self.data.low[-rb])
        for off in range(-rb - lb, 1):
            if off == -rb:
                continue
            value = float(self.data.low[off])
            if self.p.strict_pivots:
                if value <= pivot:
                    return False
            else:
                if value < pivot:
                    return False
        return True

    def _is_pivot_high_now(self) -> bool:
        rb = self.p.right_bars
        lb = self.p.left_bars
        pivot = float(self.data.high[-rb])
        for off in range(-rb - lb, 1):
            if off == -rb:
                continue
            value = float(self.data.high[off])
            if self.p.strict_pivots:
                if value >= pivot:
                    return False
            else:
                if value > pivot:
                    return False
        return True

    def _qty_from_risk(self, entry: float, stop: float) -> float:
        risk_per_unit = abs(entry - stop)
        if risk_per_unit <= 0:
            return float("nan")
        equity = max(float(self.broker.getvalue()), 0.0)
        risk_cash = equity * float(self.p.risk_pct) / 100.0
        return risk_cash / risk_per_unit

    def _submit_entry(self, side: str, qty: float, stop: float, take: float) -> None:
        if side == "long":
            order = self.buy(size=qty)
        elif side == "short":
            order = self.sell(size=qty)
        else:
            raise ValueError(side)

        self.entry_order = order
        self.entry_meta[order.ref] = dict(side=side, stop=stop, take=take, qty=qty)

    def _detect_bullish_divergence(self) -> None:
        rb = self.p.right_bars
        curr_index = self.bar_index - rb
        curr_price_low = float(self.data.low[-rb])
        curr_rsi_low = float(self.data.tv_rsi[-rb])
        curr_high = float(self.data.high[-rb])

        bullish_div = (
            self.prev_price_low is not None
            and curr_price_low < self.prev_price_low
            and curr_rsi_low > self.prev_rsi_low
        )

        if bullish_div:
            self.bull_active = True
            self.bull_trigger = self.prev_low_high
            self.bull_setup_bar = self.bar_index

            if self.p.stop_mode == "Nearest pivot":
                self.bull_stop = curr_price_low * (1.0 - self.p.stop_buffer_pct / 100.0)
            else:
                self.bull_stop = min(self.prev_price_low, curr_price_low) * (
                    1.0 - self.p.stop_buffer_pct / 100.0
                )

            self.event_log.append(
                dict(
                    dt=self.data.datetime.datetime(0),
                    event="bullish_divergence",
                    pivot_dt=self.data.datetime.datetime(-rb),
                    trigger=self.bull_trigger,
                    stop=self.bull_stop,
                    price=curr_price_low,
                    rsi=curr_rsi_low,
                )
            )

        self.prev_price_low = curr_price_low
        self.prev_rsi_low = curr_rsi_low
        self.prev_low_high = curr_high
        self.prev_low_index = curr_index

    def _detect_bearish_divergence(self) -> None:
        rb = self.p.right_bars
        curr_index = self.bar_index - rb
        curr_price_high = float(self.data.high[-rb])
        curr_rsi_high = float(self.data.tv_rsi[-rb])
        curr_low = float(self.data.low[-rb])

        bearish_div = (
            self.prev_price_high is not None
            and curr_price_high > self.prev_price_high
            and curr_rsi_high < self.prev_rsi_high
        )

        if bearish_div:
            self.bear_active = True
            self.bear_trigger = self.prev_high_low
            self.bear_setup_bar = self.bar_index

            if self.p.stop_mode == "Nearest pivot":
                self.bear_stop = curr_price_high * (1.0 + self.p.stop_buffer_pct / 100.0)
            else:
                self.bear_stop = max(self.prev_price_high, curr_price_high) * (
                    1.0 + self.p.stop_buffer_pct / 100.0
                )

            self.event_log.append(
                dict(
                    dt=self.data.datetime.datetime(0),
                    event="bearish_divergence",
                    pivot_dt=self.data.datetime.datetime(-rb),
                    trigger=self.bear_trigger,
                    stop=self.bear_stop,
                    price=curr_price_high,
                    rsi=curr_rsi_high,
                )
            )

        self.prev_price_high = curr_price_high
        self.prev_rsi_high = curr_rsi_high
        self.prev_high_low = curr_low
        self.prev_high_index = curr_index

    def _invalidate_setups(self) -> None:
        if self.bull_active:
            too_old = (self.bar_index - self.bull_setup_bar) > self.p.max_setup_bars
            stop_broken = float(self.data.low[0]) <= self.bull_stop
            if too_old or stop_broken:
                self.bull_active = False
                self.event_log.append(
                    dict(
                        dt=self.data.datetime.datetime(0),
                        event="bull_setup_cancelled",
                        reason="too_old" if too_old else "stop_broken",
                    )
                )

        if self.bear_active:
            too_old = (self.bar_index - self.bear_setup_bar) > self.p.max_setup_bars
            stop_broken = float(self.data.high[0]) >= self.bear_stop
            if too_old or stop_broken:
                self.bear_active = False
                self.event_log.append(
                    dict(
                        dt=self.data.datetime.datetime(0),
                        event="bear_setup_cancelled",
                        reason="too_old" if too_old else "stop_broken",
                    )
                )

    def _check_entries(self) -> None:
        if self.position or self.entry_order is not None:
            return

        close = float(self.data.close[0])
        long_signal = self.bull_active and close > self.bull_trigger
        short_signal = self.bear_active and close < self.bear_trigger

        if long_signal:
            entry_price = close
            risk = entry_price - self.bull_stop
            if risk > 0:
                qty = self._qty_from_risk(entry_price, self.bull_stop)
                if np.isfinite(qty) and qty > 0:
                    take = entry_price + risk * self.p.rr
                    self._submit_entry("long", qty, self.bull_stop, take)
                    self.event_log.append(
                        dict(
                            dt=self.data.datetime.datetime(0),
                            event="long_signal",
                            entry_estimate=entry_price,
                            stop=self.bull_stop,
                            take=take,
                            qty=qty,
                        )
                    )
                self.bull_active = False
            return

        if short_signal:
            entry_price = close
            risk = self.bear_stop - entry_price
            if risk > 0:
                qty = self._qty_from_risk(entry_price, self.bear_stop)
                if np.isfinite(qty) and qty > 0:
                    take = entry_price - risk * self.p.rr
                    self._submit_entry("short", qty, self.bear_stop, take)
                    self.event_log.append(
                        dict(
                            dt=self.data.datetime.datetime(0),
                            event="short_signal",
                            entry_estimate=entry_price,
                            stop=self.bear_stop,
                            take=take,
                            qty=qty,
                        )
                    )
                self.bear_active = False

    def next(self):
        self.equity_curve.append(
            dict(
                dt=self.data.datetime.datetime(0),
                equity=float(self.broker.getvalue()),
                cash=float(self.broker.getcash()),
                close=float(self.data.close[0]),
            )
        )

        if not self._enough_for_pivot():
            return

        if np.isnan(float(self.data.tv_rsi[-self.p.right_bars])):
            return

        if self._is_pivot_low_now():
            self._detect_bullish_divergence()

        if self._is_pivot_high_now():
            self._detect_bearish_divergence()

        self._invalidate_setups()
        self._check_entries()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.ref in self.entry_meta:
            meta = self.entry_meta.pop(order.ref)
            self.entry_order = None

            if order.status == order.Completed:
                side = meta["side"]
                size = abs(float(order.executed.size))
                stop = float(meta["stop"])
                take = float(meta["take"])

                self.current_trade_side = side
                self.current_trade_entry_dt = self.data.datetime.datetime(0)
                self.current_trade_entry_bar = self.bar_index
                self.current_trade_entry_price = float(order.executed.price)

                if side == "long":
                    self.stop_order = self.sell(size=size, exectype=bt.Order.Stop, price=stop)
                    self.limit_order = self.sell(
                        size=size,
                        exectype=bt.Order.Limit,
                        price=take,
                        oco=self.stop_order,
                    )
                else:
                    self.stop_order = self.buy(size=size, exectype=bt.Order.Stop, price=stop)
                    self.limit_order = self.buy(
                        size=size,
                        exectype=bt.Order.Limit,
                        price=take,
                        oco=self.stop_order,
                    )

                self.event_log.append(
                    dict(
                        dt=self.data.datetime.datetime(0),
                        event=f"{side}_entry_filled",
                        fill_price=float(order.executed.price),
                        size=size,
                        stop=stop,
                        take=take,
                    )
                )
            else:
                self.event_log.append(
                    dict(
                        dt=self.data.datetime.datetime(0),
                        event="entry_rejected_or_cancelled",
                        status=order.getstatusname(),
                        meta=meta,
                    )
                )

        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            if order == self.stop_order:
                self.stop_order = None
            if order == self.limit_order:
                self.limit_order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_records.append(
                dict(
                    entry_dt=self.current_trade_entry_dt,
                    exit_dt=self.data.datetime.datetime(0),
                    side=self.current_trade_side,
                    entry_price=self.current_trade_entry_price,
                    pnl=float(trade.pnl),
                    pnlcomm=float(trade.pnlcomm),
                    bars=(self.bar_index - self.current_trade_entry_bar)
                    if self.current_trade_entry_bar is not None
                    else None,
                )
            )
            self.current_trade_side = None
            self.current_trade_entry_dt = None
            self.current_trade_entry_bar = None
            self.current_trade_entry_price = None
