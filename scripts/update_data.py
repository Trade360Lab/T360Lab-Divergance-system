from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.bybit_loader import load_bybit_klines
from src.data.cache import load_ohlcv_cache, save_ohlcv_cache, update_ohlcv_cache
from src.data.normalizer import normalize_ohlcv_df
from src.data.validators import validate_ohlcv_df


def _freq_from_interval(interval: str) -> str:
    if str(interval).isdigit():
        return f"{interval}min"
    return str(interval)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/data.yaml")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)["data"]

    cache_path = PROJECT_ROOT / config["cache_path"]
    raw = load_bybit_klines(
        category=config["category"],
        symbol=config["symbol"],
        interval=config["interval"],
        start_time=config["start_time"],
        end_time=config["end_time"],
    )
    normalized = normalize_ohlcv_df(raw)
    existing = load_ohlcv_cache(cache_path)
    merged = update_ohlcv_cache(existing, normalized)
    validate_ohlcv_df(merged, freq=_freq_from_interval(config["interval"]))
    save_ohlcv_cache(merged, cache_path)
    print(f"saved {len(merged)} bars to {cache_path}")


if __name__ == "__main__":
    main()
