PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install-dev lint format typecheck test test-unit-cov test-integration test-integration-fast test-integration-extended generate-cdef build check

install-dev:
	$(PIP) install -U pip
	$(PIP) install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy pyaeron

test:
	$(PYTHON) -m pytest -m "not integration"

test-unit-cov:
	$(PYTHON) -m pytest -m "not integration" --cov=pyaeron --cov-report=term --cov-fail-under=75

test-integration:
	$(PYTHON) -m pytest -m integration tests/integration

test-integration-fast:
	$(PYTHON) -m pytest -m "integration and not integration_extended" tests/integration

test-integration-extended:
	$(PYTHON) -m pytest -m integration_extended tests/integration

generate-cdef:
	$(PYTHON) scripts/generate_cdef.py

build:
	$(PYTHON) -m build

check: lint typecheck test test-integration
