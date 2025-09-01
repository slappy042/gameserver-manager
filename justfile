# Development commands for gameserver-manager
# Usage: just <command>

# Default recipe - show help
default:
    @just --list

# Set up development environment
setup:
    @echo "Setting up development environment..."
    uv sync
    @echo "✓ Development environment ready"

# Install dependencies
install:
    uv sync

# Update dependencies
update:
    uv sync --upgrade

# Run the CLI tool
run *args:
    uv run gameserver {{args}}

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=gameserver --cov-report=html

# Type checking
check:
    uv run mypy gameserver/

# Linting and formatting
lint:
    uv run ruff check .

# Format code
format:
    uv run ruff format .

# Run all checks (lint, format, type check, test)
ci: lint format check test

# Build the package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist/
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -name "*.pyc" -delete

# Install in development mode
dev-install:
    uv pip install -e .

# Run with nix develop (for system dependencies)
nix-run *args:
    nix develop -c uv run gameserver {{args}}

# Run tests in nix environment
nix-test:
    nix develop -c uv run pytest

# Show project info
info:
    @echo "=== Gameserver Manager Development ==="
    @echo "Python version: $(python --version)"
    @echo "UV version: $(uv --version)"
    @echo "Project location: $(pwd)"
    @echo ""
    @echo "Available commands:"
    @just --list
