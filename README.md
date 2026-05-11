# T360Lab-Divergance-system (v1)

## Telegram signal formatter

Signal-only Telegram messages are formatted without sending anything to Telegram:

```python
from src.notifications.telegram_formatter import format_signal_message

payload = {
    "event": "entry_confirmed",
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "side": "long",
    "datetime": "2026-05-11 16:15:00 UTC",
    "entry": 80820.6,
    "stop_loss": 80100.0,
    "take_profit": 81901.5,
    "risk_pct": 3.0,
    "rr": 1.5,
    "qty": 0.42,
    "risk_amount": 300.0,
}

message = format_signal_message(payload)
```

Use the returned string with Telegram `parse_mode="HTML"`. The formatter is pure Python and does not include a Telegram API client.
