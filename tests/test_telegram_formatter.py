from src.notifications.telegram_formatter import format_signal_message


def entry_payload():
    return {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "side": "long",
        "event": "entry_confirmed",
        "datetime": "2026-05-11 16:15:00 UTC",
        "entry": 80820.6,
        "stop_loss": 80100.0,
        "take_profit": 81901.5,
        "risk_pct": 3.0,
        "rr": 1.5,
        "qty": 0.42,
        "equity": 10000.0,
        "risk_amount": 300.0,
        "setup_type": "bullish_rsi_divergence",
        "stop_mode": "nearest_pivot",
        "stop_buffer": 0.0,
    }


def test_format_entry_confirmed_contains_levels():
    message = format_signal_message(entry_payload())

    assert isinstance(message, str)
    assert "LONG ENTRY CONFIRMED BTCUSDT 15m" in message
    assert "Entry: 80,820.6" in message
    assert "Stop-loss: 80,100.0" in message
    assert "Take-profit: 81,901.5" in message
    assert "Risk amount: +300.00 USDT" in message
    assert "Qty: 0.4200" in message


def test_format_setup_new_long():
    message = format_signal_message(
        {
            "event": "setup_new",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "side": "long",
            "datetime": "2026-05-11 14:45:00 UTC",
            "setup_type": "bullish_rsi_divergence",
            "rsi_length": 13,
            "pivot_left": 3,
            "pivot_right": 5,
            "div_start_price": 80820.6,
            "div_end_price": 80240.2,
            "div_start_rsi": 31.4,
            "div_end_rsi": 38.7,
            "breakout_level": 80820.6,
            "stop_loss_candidate": 80100.0,
            "max_bars_to_wait": 90,
            "bars_waited": 0,
        }
    )

    assert "🚀" in message
    assert "LONG SETUP NEW BTCUSDT 15m" in message
    assert "bullish_rsi_divergence" in message
    assert "Start RSI: 31.40" in message
    assert "Breakout level: 80,820.6" in message


def test_format_trade_closed_tp():
    payload = {
        "event": "trade_closed",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "side": "long",
        "datetime": "2026-05-11 20:30:00 UTC",
        "close_reason": "tp",
        "entry": 80820.6,
        "exit": 81901.5,
        "stop_loss": 80100.0,
        "take_profit": 81901.5,
        "qty": 0.42,
        "pnl": 454.0,
        "pnl_pct": 4.54,
        "r_multiple": 1.5,
        "duration": "4h 15m",
    }

    message = format_signal_message(payload)

    assert "✅" in message
    assert "LONG TAKE PROFIT BTCUSDT 15m" in message
    assert "PnL: +454.00 USDT" in message
    assert "R: +1.50R" in message


def test_format_trade_closed_sl():
    payload = {
        "event": "trade_closed",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "side": "short",
        "close_reason": "sl",
        "entry": 80820.6,
        "exit": 81300.0,
        "qty": 0.42,
        "pnl": -300.0,
        "pnl_pct": -3.0,
        "r_multiple": -1.0,
    }

    message = format_signal_message(payload)

    assert "🛑" in message
    assert "SHORT STOP LOSS BTCUSDT 15m" in message
    assert "PnL: -300.00 USDT" in message
    assert "R: -1.00R" in message


def test_format_status():
    message = format_signal_message(
        {
            "event": "status",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "side": "long",
            "datetime": "2026-05-11 18:00:00 UTC",
            "entry": 80820.6,
            "current_price": 81350.0,
            "stop_loss": 80100.0,
            "take_profit": 81901.5,
            "qty": 0.42,
            "unrealized_pnl": 222.35,
            "unrealized_pnl_pct": 2.22,
            "r_multiple": 0.73,
            "distance_to_sl_pct": 1.54,
            "distance_to_tp_pct": 0.68,
            "time_in_trade": "1h 45m",
        }
    )

    assert "POSITION STATUS" in message
    assert "Current: 81,350.0" in message
    assert "Unrealized PnL: +222.35 USDT" in message
    assert "R: +0.73R" in message


def test_format_daily_summary():
    message = format_signal_message(
        {
            "event": "daily_summary",
            "symbol": "BTCUSDT",
            "period": "2026-05-11",
            "datetime": "2026-05-11 23:59:00 UTC",
            "trades": 4,
            "winrate": 50.0,
            "net_pnl": 320.0,
            "net_pnl_pct": 3.2,
            "max_drawdown_pct": -1.8,
            "long": {"trades": 2, "winrate": 50.0, "net_pnl": 120.0},
            "short": {"trades": 2, "winrate": 50.0, "net_pnl": 200.0},
        }
    )

    assert "DAILY SUMMARY BTCUSDT" in message
    assert "Trades: 4" in message
    assert "Winrate: +50.00%" in message
    assert "Net PnL: +320.00 USDT" in message
    assert "Long: 2 trades, +50.00% winrate, +120.00 USDT" in message
    assert "Short: 2 trades, +50.00% winrate, +200.00 USDT" in message


def test_unknown_event_returns_warning():
    message = format_signal_message(
        {
            "event": "new_weird_event",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
        }
    )

    assert "WARNING BTCUSDT 15m" in message
    assert "unknown_event" in message
    assert "Unknown event: new_weird_event" in message


def test_html_escape():
    message = format_signal_message(
        {
            "event": "warning",
            "symbol": "BTC<USDT>",
            "timeframe": "15m",
            "warning_type": "api_error",
            "message": "<b>bad & unsafe</b>",
        }
    )

    assert "BTC&lt;USDT&gt;" in message
    assert "&lt;b&gt;bad &amp; unsafe&lt;/b&gt;" in message
    assert "<b>bad & unsafe</b>" not in message


def test_missing_values_do_not_crash():
    message = format_signal_message({"event": "entry_confirmed"})

    assert isinstance(message, str)
    assert "ENTRY CONFIRMED" in message
    assert "Entry: —" in message
    assert "Qty: —" in message
    assert "Time: —" in message


def test_short_side_header():
    payload = entry_payload()
    payload["side"] = "short"
    message = format_signal_message(payload)

    assert "🔻" in message
    assert "SHORT ENTRY CONFIRMED BTCUSDT 15m" in message
    assert "LONG ENTRY CONFIRMED" not in message
