.PHONY: help install test lint format clean init run

help:
	@echo "Local Knowledge Base - Makefile Commands"
	@echo ""
	@echo "  make install    Install dependencies"
	@echo "  make init       Initialize database"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linters"
	@echo "  make format     Format code"
	@echo "  make clean      Clean temporary files"
	@echo "  make run        Run development server"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

init:
	python -m app.cli init

test:
	pytest -v --cov=app --cov-report=html --cov-report=term

lint:
	ruff check app tests
	mypy app

format:
	black app tests
	ruff check --fix app tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

run:
	@echo "⚠️  Web server not yet implemented"
	@echo "Use CLI: python -m app.cli --help"
