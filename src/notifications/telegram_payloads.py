from __future__ import annotations

from typing import Any, Literal, TypedDict

from src.notifications.telegram_constants import (
    CLOSE_CANCELLED,
    CLOSE_EXPIRED,
    CLOSE_MANUAL,
    CLOSE_SL,
    CLOSE_TP,
    EVENT_DAILY_SUMMARY,
    EVENT_ENTRY_CONFIRMED,
    EVENT_ERROR,
    EVENT_LEVELS,
    EVENT_SETUP_CANCELLED,
    EVENT_SETUP_NEW,
    EVENT_STATUS,
    EVENT_TRADE_CLOSED,
    EVENT_WARNING,
    EVENT_WEEKLY_SUMMARY,
    SIDE_LONG,
    SIDE_SHORT,
    WARNING_API_ERROR,
    WARNING_MISSED_CANDLES,
    WARNING_POSITION_ALREADY_OPEN,
    WARNING_RISK_TOO_HIGH,
    WARNING_SIGNAL_NOT_CONFIRMED,
    WARNING_STALE_DATA,
    WARNING_UNKNOWN_EVENT,
)

Side = Literal["long", "short"]
SignalEvent = Literal[
    EVENT_SETUP_NEW,
    EVENT_ENTRY_CONFIRMED,
    EVENT_LEVELS,
    EVENT_TRADE_CLOSED,
    EVENT_SETUP_CANCELLED,
    EVENT_STATUS,
    EVENT_DAILY_SUMMARY,
    EVENT_WEEKLY_SUMMARY,
    EVENT_WARNING,
    EVENT_ERROR,
]
CloseReason = Literal[CLOSE_TP, CLOSE_SL, CLOSE_MANUAL, CLOSE_EXPIRED, CLOSE_CANCELLED]
WarningType = Literal[
    WARNING_MISSED_CANDLES,
    WARNING_API_ERROR,
    WARNING_STALE_DATA,
    WARNING_SIGNAL_NOT_CONFIRMED,
    WARNING_RISK_TOO_HIGH,
    WARNING_POSITION_ALREADY_OPEN,
    WARNING_UNKNOWN_EVENT,
]


class BasePayload(TypedDict, total=False):
    event: str
    symbol: str
    timeframe: str
    side: str
    datetime: str
    message: str


class SetupNewPayload(BasePayload, total=False):
    event: Literal[EVENT_SETUP_NEW]
    setup_type: str
    rsi_length: int
    pivot_left: int
    pivot_right: int
    div_start_price: float
    div_end_price: float
    div_start_rsi: float
    div_end_rsi: float
    breakout_level: float
    stop_loss_candidate: float
    max_bars_to_wait: int
    bars_waited: int


class EntryConfirmedPayload(BasePayload, total=False):
    event: Literal[EVENT_ENTRY_CONFIRMED]
    entry: float
    stop_loss: float
    take_profit: float
    risk_pct: float
    rr: float
    qty: float
    equity: float
    risk_amount: float
    setup_type: str
    stop_mode: str
    stop_buffer: float


class LevelsPayload(BasePayload, total=False):
    event: Literal[EVENT_LEVELS]
    entry: float
    stop_loss: float
    take_profit: float
    breakout_level: float
    rr: float
    risk_pct: float


class TradeClosedPayload(BasePayload, total=False):
    event: Literal[EVENT_TRADE_CLOSED]
    close_reason: str
    entry: float
    exit: float
    stop_loss: float
    take_profit: float
    qty: float
    pnl: float
    pnl_pct: float
    r_multiple: float
    duration: str


class SetupCancelledPayload(BasePayload, total=False):
    event: Literal[EVENT_SETUP_CANCELLED]
    reason: str
    setup_type: str
    breakout_level: float
    stop_loss_candidate: float
    bars_waited: int
    max_bars_to_wait: int


class StatusPayload(BasePayload, total=False):
    event: Literal[EVENT_STATUS]
    entry: float
    current_price: float
    stop_loss: float
    take_profit: float
    qty: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    r_multiple: float
    distance_to_sl_pct: float
    distance_to_tp_pct: float
    time_in_trade: str


class SummarySideBreakdown(TypedDict, total=False):
    trades: int
    winrate: float
    net_pnl: float


class SummaryPayload(BasePayload, total=False):
    event: Literal[EVENT_DAILY_SUMMARY, EVENT_WEEKLY_SUMMARY]
    period: str
    trades: int
    winrate: float
    net_pnl: float
    net_pnl_pct: float
    max_drawdown_pct: float
    long: SummarySideBreakdown
    short: SummarySideBreakdown


class WarningPayload(BasePayload, total=False):
    event: Literal[EVENT_WARNING, EVENT_ERROR]
    warning_type: str
    error_type: str
    details: str
    expected_last_bar: str
    actual_last_bar: str
    missed_count: int


SignalPayload = (
    SetupNewPayload
    | EntryConfirmedPayload
    | LevelsPayload
    | TradeClosedPayload
    | SetupCancelledPayload
    | StatusPayload
    | SummaryPayload
    | WarningPayload
    | dict[str, Any]
)
