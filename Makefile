test:
	pytest tests/

test-fast:
	pytest tests/ -m "not slow and not integration"

test-regression:
	pytest tests/ -m regression

update-data:
	python scripts/update_data.py --config config/data.yaml

backtest:
	python scripts/run_backtest.py --strategy-config config/strategy.yaml --backtest-config config/backtest.yaml --data data/processed/BTCUSDT_15.parquet

wfa:
	python scripts/run_wfa.py --strategy-config config/strategy.yaml --optimization-config config/optimization.yaml --data data/processed/BTCUSDT_15.parquet

robustness:
	python scripts/run_robustness.py --data data/processed/BTCUSDT_15.parquet

docker-build:
	docker build -t tradelab-signals:test .
