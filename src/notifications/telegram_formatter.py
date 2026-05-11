from __future__ import annotations

from html import escape
from typing import Any

from src.notifications.telegram_constants import (
    CLOSE_CANCELLED,
    CLOSE_EXPIRED,
    CLOSE_MANUAL,
    CLOSE_SL,
    CLOSE_TP,
    DEFAULT_CURRENCY,
    DEFAULT_SYMBOL,
    DEFAULT_TIMEFRAME,
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

MISSING = "—"


def h(value: Any) -> str:
    if value is None:
        return MISSING
    if value == "":
        return MISSING
    return escape(str(value), quote=True)


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_price(value: Any, digits: int = 1) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:,.{digits}f}"


def fmt_qty(value: Any, digits: int = 4) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:,.{digits}f}"


def fmt_pct(value: Any, digits: int = 2) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:+.{digits}f}%"


def fmt_money(value: Any, currency: str = DEFAULT_CURRENCY) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:+,.2f} {h(currency)}"


def fmt_r(value: Any) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:+.2f}R"


def fmt_rsi(value: Any) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:.2f}"


def fmt_plain_number(value: Any, digits: int = 1) -> str:
    number = _number(value)
    if number is None:
        return MISSING
    return f"{number:.{digits}f}"


def side_label(side: Any) -> str:
    normalized = str(side or "").lower()
    if normalized == SIDE_LONG:
        return "LONG"
    if normalized == SIDE_SHORT:
        return "SHORT"
    return "SIDE"


def side_emoji(side: Any) -> str:
    normalized = str(side or "").lower()
    if normalized == SIDE_LONG:
        return "🚀"
    if normalized == SIDE_SHORT:
        return "🔻"
    return "📍"


def close_emoji(reason: Any) -> str:
    normalized = str(reason or "").lower()
    return {
        CLOSE_TP: "✅",
        CLOSE_SL: "🛑",
        CLOSE_MANUAL: "✋",
        CLOSE_EXPIRED: "⌛",
        CLOSE_CANCELLED: "🚫",
    }.get(normalized, "🏁")


def close_label(reason: Any) -> str:
    normalized = str(reason or "").lower()
    return {
        CLOSE_TP: "TAKE PROFIT",
        CLOSE_SL: "STOP LOSS",
        CLOSE_MANUAL: "MANUAL CLOSE",
        CLOSE_EXPIRED: "EXPIRED",
        CLOSE_CANCELLED: "CANCELLED",
    }.get(normalized, "CLOSED")


def warning_emoji(warning_type: Any) -> str:
    normalized = str(warning_type or "").lower()
    return {
        WARNING_MISSED_CANDLES: "🕯️",
        WARNING_API_ERROR: "🔌",
        WARNING_STALE_DATA: "⏱️",
        WARNING_SIGNAL_NOT_CONFIRMED: "⚠️",
        WARNING_RISK_TOO_HIGH: "🚧",
        WARNING_POSITION_ALREADY_OPEN: "🔒",
        WARNING_UNKNOWN_EVENT: "❓",
    }.get(normalized, "⚠️")


def _symbol(payload: dict[str, Any]) -> str:
    return h(payload.get("symbol", DEFAULT_SYMBOL))


def _timeframe(payload: dict[str, Any]) -> str:
    return h(payload.get("timeframe", DEFAULT_TIMEFRAME))


def format_header(emoji: str, title: str, payload: dict[str, Any]) -> str:
    return f"{emoji} <b>{h(title)} {_symbol(payload)} {_timeframe(payload)}</b>"


def _time_line(payload: dict[str, Any]) -> str:
    return f"Time: {h(payload.get('datetime'))}"


def _section(title: str, rows: list[tuple[str, str]]) -> str:
    lines = [h(title)]
    for label, value in rows:
        lines.append(f"• {h(label)}: {value}")
    return "\n".join(lines)


def format_setup_new(payload: dict[str, Any]) -> str:
    side = payload.get("side")
    header = format_header(side_emoji(side), f"{side_label(side)} SETUP NEW", payload)
    intro = h(payload.get("setup_type", "RSI divergence setup detected"))
    divergence = _section(
        "Divergence",
        [
            ("Start price", fmt_price(payload.get("div_start_price"))),
            ("End price", fmt_price(payload.get("div_end_price"))),
            ("Start RSI", fmt_rsi(payload.get("div_start_rsi"))),
            ("End RSI", fmt_rsi(payload.get("div_end_rsi"))),
        ],
    )
    levels = _section(
        "Setup levels",
        [
            ("Breakout level", fmt_price(payload.get("breakout_level"))),
            ("Stop candidate", fmt_price(payload.get("stop_loss_candidate"))),
        ],
    )
    params = _section(
        "Parameters",
        [
            ("RSI length", h(payload.get("rsi_length"))),
            ("Pivot left/right", f"{h(payload.get('pivot_left'))}/{h(payload.get('pivot_right'))}"),
            ("Bars waited", h(payload.get("bars_waited"))),
            ("Max bars", h(payload.get("max_bars_to_wait"))),
        ],
    )
    return "\n\n".join([header, intro, divergence, levels, params, _time_line(payload)])


def format_entry_confirmed(payload: dict[str, Any]) -> str:
    side = payload.get("side")
    header = format_header(side_emoji(side), f"{side_label(side)} ENTRY CONFIRMED", payload)
    intro = "Breakout candle closed beyond setup level"
    levels = _section(
        "Trade levels",
        [
            ("Entry", fmt_price(payload.get("entry"))),
            ("Stop-loss", fmt_price(payload.get("stop_loss"))),
            ("Take-profit", fmt_price(payload.get("take_profit"))),
        ],
    )
    risk = _section(
        "Risk",
        [
            ("Risk", fmt_pct(payload.get("risk_pct"))),
            ("Risk amount", fmt_money(payload.get("risk_amount"))),
            ("RR", h(payload.get("rr"))),
            ("Qty", fmt_qty(payload.get("qty"))),
        ],
    )
    stop_model = _section(
        "Stop model",
        [
            ("Mode", h(payload.get("stop_mode"))),
            ("Buffer", fmt_plain_number(payload.get("stop_buffer"), digits=1)),
        ],
    )
    return "\n\n".join([header, intro, levels, risk, stop_model, _time_line(payload)])


def format_levels(payload: dict[str, Any]) -> str:
    side = payload.get("side")
    header = format_header("📐", f"{side_label(side)} LEVELS", payload)
    levels = _section(
        "Trade levels",
        [
            ("Entry", fmt_price(payload.get("entry"))),
            ("Breakout level", fmt_price(payload.get("breakout_level"))),
            ("Stop-loss", fmt_price(payload.get("stop_loss"))),
            ("Take-profit", fmt_price(payload.get("take_profit"))),
            ("RR", h(payload.get("rr"))),
            ("Risk", fmt_pct(payload.get("risk_pct"))),
        ],
    )
    return "\n\n".join([header, levels, _time_line(payload)])


def format_trade_closed(payload: dict[str, Any]) -> str:
    reason = payload.get("close_reason")
    side = payload.get("side")
    header = format_header(close_emoji(reason), f"{side_label(side)} {close_label(reason)}", payload)
    prices = _section(
        "Trade",
        [
            ("Entry", fmt_price(payload.get("entry"))),
            ("Exit", fmt_price(payload.get("exit"))),
            ("Stop-loss", fmt_price(payload.get("stop_loss"))),
            ("Take-profit", fmt_price(payload.get("take_profit"))),
            ("Qty", fmt_qty(payload.get("qty"))),
        ],
    )
    result = _section(
        "Result",
        [
            ("PnL", fmt_money(payload.get("pnl"))),
            ("PnL %", fmt_pct(payload.get("pnl_pct"))),
            ("R", fmt_r(payload.get("r_multiple"))),
            ("Duration", h(payload.get("duration"))),
        ],
    )
    return "\n\n".join([header, prices, result, _time_line(payload)])


def format_setup_cancelled(payload: dict[str, Any]) -> str:
    side = payload.get("side")
    header = format_header("🚫", f"{side_label(side)} SETUP CANCELLED", payload)
    details = _section(
        "Cancellation",
        [
            ("Reason", h(payload.get("reason"))),
            ("Setup", h(payload.get("setup_type"))),
            ("Breakout level", fmt_price(payload.get("breakout_level"))),
            ("Stop candidate", fmt_price(payload.get("stop_loss_candidate"))),
            ("Bars waited", h(payload.get("bars_waited"))),
            ("Max bars", h(payload.get("max_bars_to_wait"))),
        ],
    )
    return "\n\n".join([header, details, _time_line(payload)])


def format_status(payload: dict[str, Any]) -> str:
    side = payload.get("side")
    header = format_header("📊", f"{side_label(side)} POSITION STATUS", payload)
    levels = _section(
        "Position",
        [
            ("Entry", fmt_price(payload.get("entry"))),
            ("Current", fmt_price(payload.get("current_price"))),
            ("Stop-loss", fmt_price(payload.get("stop_loss"))),
            ("Take-profit", fmt_price(payload.get("take_profit"))),
            ("Qty", fmt_qty(payload.get("qty"))),
        ],
    )
    live = _section(
        "Live result",
        [
            ("Unrealized PnL", fmt_money(payload.get("unrealized_pnl"))),
            ("Unrealized %", fmt_pct(payload.get("unrealized_pnl_pct"))),
            ("R", fmt_r(payload.get("r_multiple"))),
            ("Time in trade", h(payload.get("time_in_trade"))),
        ],
    )
    distances = _section(
        "Distance",
        [
            ("To SL", fmt_pct(payload.get("distance_to_sl_pct"))),
            ("To TP", fmt_pct(payload.get("distance_to_tp_pct"))),
        ],
    )
    return "\n\n".join([header, levels, live, distances, _time_line(payload)])


def _format_side_breakdown(name: str, data: Any) -> str:
    row = data if isinstance(data, dict) else {}
    return (
        f"• {h(name)}: {h(row.get('trades'))} trades, "
        f"{fmt_pct(row.get('winrate'))} winrate, "
        f"{fmt_money(row.get('net_pnl'))}"
    )


def _format_summary(payload: dict[str, Any], title: str, emoji: str) -> str:
    header = format_header(emoji, title, payload)
    totals = _section(
        "Total",
        [
            ("Period", h(payload.get("period"))),
            ("Trades", h(payload.get("trades"))),
            ("Winrate", fmt_pct(payload.get("winrate"))),
            ("Net PnL", fmt_money(payload.get("net_pnl"))),
            ("Net PnL %", fmt_pct(payload.get("net_pnl_pct"))),
            ("Max drawdown", fmt_pct(payload.get("max_drawdown_pct"))),
        ],
    )
    breakdown = "\n".join(
        [
            "Breakdown",
            _format_side_breakdown("Long", payload.get("long")),
            _format_side_breakdown("Short", payload.get("short")),
        ]
    )
    return "\n\n".join([header, totals, breakdown, _time_line(payload)])


def format_daily_summary(payload: dict[str, Any]) -> str:
    return _format_summary(payload, "DAILY SUMMARY", "📅")


def format_weekly_summary(payload: dict[str, Any]) -> str:
    return _format_summary(payload, "WEEKLY SUMMARY", "🗓️")


def format_warning(payload: dict[str, Any]) -> str:
    event = str(payload.get("event") or EVENT_WARNING).lower()
    warning_type = payload.get("warning_type") or payload.get("error_type") or WARNING_UNKNOWN_EVENT
    title = "ERROR" if event == EVENT_ERROR else "WARNING"
    header = format_header(warning_emoji(warning_type), title, payload)
    details = _section(
        "Details",
        [
            ("Type", h(warning_type)),
            ("Message", h(payload.get("message") or payload.get("details"))),
            ("Expected last bar", h(payload.get("expected_last_bar"))),
            ("Actual last bar", h(payload.get("actual_last_bar"))),
            ("Missed candles", h(payload.get("missed_count"))),
        ],
    )
    return "\n\n".join([header, details, _time_line(payload)])


def _unknown_event_warning(payload: dict[str, Any]) -> str:
    warning_payload = dict(payload)
    warning_payload["event"] = EVENT_WARNING
    warning_payload["warning_type"] = WARNING_UNKNOWN_EVENT
    warning_payload["message"] = f"Unknown event: {payload.get('event', MISSING)}"
    return format_warning(warning_payload)


def format_signal_message(payload: dict[str, Any]) -> str:
    event = str(payload.get("event") or "").lower()
    formatters = {
        EVENT_SETUP_NEW: format_setup_new,
        EVENT_ENTRY_CONFIRMED: format_entry_confirmed,
        EVENT_LEVELS: format_levels,
        EVENT_TRADE_CLOSED: format_trade_closed,
        EVENT_SETUP_CANCELLED: format_setup_cancelled,
        EVENT_STATUS: format_status,
        EVENT_DAILY_SUMMARY: format_daily_summary,
        EVENT_WEEKLY_SUMMARY: format_weekly_summary,
        EVENT_WARNING: format_warning,
        EVENT_ERROR: format_warning,
    }
    formatter = formatters.get(event)
    if formatter is None:
        return _unknown_event_warning(payload)
    return formatter(payload)
