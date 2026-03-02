PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install-dev lint format typecheck test test-integration test-integration-fast test-integration-extended generate-cdef check

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

test-integration-fast:
	pytest -m "integration and not integration_extended" tests/integration

test-integration-extended:
	pytest -m integration_extended tests/integration

generate-cdef:
	$(PYTHON) scripts/generate_cdef.py

check: lint typecheck test test-integration
