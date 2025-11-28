.PHONY: install lint fmt typecheck test test-cov serve cli check clean help

# Default target
help:
	@echo "Gemini Code Assist MCP - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  make lint         Run linter (ruff check)"
	@echo "  make fmt          Format code (ruff format)"
	@echo "  make typecheck    Run type checker (mypy)"
	@echo "  make check        Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo ""
	@echo "Running:"
	@echo "  make serve        Start MCP server"
	@echo "  make cli          Run CLI status check"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        Remove build artifacts"

# Setup
install:
	uv sync --dev

# Code quality
lint:
	uv run ruff check .

fmt:
	uv run ruff format .

typecheck:
	uv run mypy .

# Run all checks (for CI)
check: lint typecheck test
	@echo "All checks passed!"

# Testing
test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Running
serve:
	uv run python src/main.py

cli:
	uv run gemini-mcp-cli status check

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
