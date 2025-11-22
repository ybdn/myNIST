.PHONY: help install run test clean dev lint format

# Default target
help:
	@echo "NIST Studio - Makefile Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run application in development mode"
	@echo "  make test       - Run tests with pytest"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make dev        - Install in development mode"
	@echo "  make lint       - Run linters (flake8)"
	@echo "  make format     - Format code with black"
	@echo "  make venv       - Create virtual environment"

# Create virtual environment
venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "Dependencies installed successfully"

# Install in development mode
dev:
	pip install -e .
	pip install pytest pytest-qt pytest-cov flake8 black
	@echo "Development environment ready"

# Run application
run:
	python -m mynist

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-coverage:
	pytest --cov=mynist --cov-report=html tests/
	@echo "Coverage report generated in htmlcov/index.html"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf mynist/__pycache__
	rm -rf mynist/*/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned build artifacts"

# Lint code
lint:
	flake8 mynist/ --max-line-length=100 --ignore=E501,W503

# Format code
format:
	black mynist/ tests/ --line-length=100

# Quick test and run
quick: test run

# Development setup from scratch
setup: venv install dev
	@echo "Development setup complete!"
	@echo "Activate environment: source venv/bin/activate"
