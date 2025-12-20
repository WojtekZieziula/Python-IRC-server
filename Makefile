install:
	uv sync

format:
	uv run ruff format src

lint:
	uv run ruff check src
	uv run mypy src

run:
	uv run python -m src.main --config config.yaml

clean:
	rm -rf .venv .mypy_cache .ruff_cache __pycache__ src/__pycache__
