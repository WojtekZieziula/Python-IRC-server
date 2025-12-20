PYTHON = python3.11
VENV = .venv
BIN = $(VENV)/bin

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e .[dev]

format:
	$(BIN)/ruff format src

lint:
	$(BIN)/ruff check src
	$(BIN)/mypy src

run:
	$(PYTHON) -m src.main --config config.yaml

clean:
	rm -rf $(VENV) .mypy_cache .ruff_cache __pycache__ src/__pycache__