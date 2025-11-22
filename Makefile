# Makefile for rpip development tasks

.PHONY: help install install-dev test test-verbose test-coverage clean lint format

help:
	@echo "rpip Development Commands"
	@echo "========================="
	@echo "install          - Install package in editable mode"
	@echo "install-dev      - Install package with dev dependencies"
	@echo "test             - Run test suite"
	@echo "test-verbose     - Run test suite with verbose output"
	@echo "test-coverage    - Run tests with coverage report"
	@echo "clean            - Remove build artifacts and cache files"
	@echo "lint             - Run linting checks (if tools installed)"
	@echo "format           - Format code (if tools installed)"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-verbose:
	pytest -v

test-coverage:
	pytest --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.whl" -delete

lint:
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 main.py tests/; \
	else \
		echo "flake8 not installed. Run: pip install flake8"; \
	fi

format:
	@if command -v black >/dev/null 2>&1; then \
		black main.py tests/; \
	else \
		echo "black not installed. Run: pip install black"; \
	fi
