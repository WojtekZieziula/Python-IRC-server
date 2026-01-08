.PHONY: install format lint test run docker-build docker-up clean

install:
	uv sync
	uv run mypy --install-types --non-interactive src

format:
	uv run ruff format src tests
	uv run ruff check src --fix

lint:
	uv run ruff check src tests
	uv run mypy src tests

test:
	uv run pytest -v

run:
	uv run python -m src.main --config config.yaml

docker-build:
	docker-compose build

docker-up:
	docker-compose up

clean:
	rm -rf .venv .mypy_cache .ruff_cache .pytest_cache __pycache__ src/__pycache__ tests/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
