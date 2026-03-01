PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install-dev lint format typecheck test test-integration check

install-dev:
	$(PIP) install -U pip
	$(PIP) install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy pyaeron

test:
	pytest -m "not integration"

test-integration:
	pytest -m integration tests/integration

check: lint typecheck test test-integration
