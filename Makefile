# Makefile for ClamAV GUI

.PHONY: test test-verbose test-coverage test-specific test-gui test-integration test-performance test-isolation install clean help lint

# Default target
help:
	@echo "Available commands:"
	@echo "  test              - Run all tests with coverage"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  test-coverage     - Run tests with detailed coverage report"
	@echo "  test-specific     - Run specific test (usage: make test-specific TEST=test_lang_manager.py)"
	@echo "  test-gui          - Run GUI integration tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-performance  - Run performance and benchmark tests"
	@echo "  test-isolation    - Run ClamAV isolation tests"
	@echo "  install           - Install development dependencies"
	@echo "  clean             - Clean up generated files"
	@echo "  lint              - Run code linting"

# Install development dependencies
install:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-qt pytest-benchmark flake8 black

# Run all tests with coverage
test:
	python -m pytest --cov=clamav_gui --cov-report=term-missing --cov-report=html --cov-report=xml

# Run tests with verbose output
test-verbose:
	python -m pytest -v --cov=clamav_gui --cov-report=term-missing

# Run tests with detailed coverage report
test-coverage:
	python -m pytest --cov=clamav_gui --cov-report=term-missing:skip-covered --cov-report=html --cov-report=xml
	@echo "Coverage report generated in htmlcov/index.html"

# Run specific test file
test-specific:
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-specific TEST=test_file.py"; \
		exit 1; \
	fi
	python -m pytest $(TEST) -v

# Run GUI tests only
test-gui:
	python -m pytest -m gui -v --cov=clamav_gui --cov-report=term-missing

# Run integration tests only
test-integration:
	python -m pytest -m integration -v --cov=clamav_gui --cov-report=term-missing

# Run performance tests only
test-performance:
	python -m pytest -m performance or benchmark -v --tb=short

# Run isolation tests only
test-isolation:
	python -m pytest -m isolation or clamav_mock -v --cov=clamav_gui --cov-report=term-missing

# Clean up generated files
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Run linting
lint:
	flake8 clamav_gui/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 clamav_gui/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
