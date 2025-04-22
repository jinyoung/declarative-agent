.PHONY: install dev-install lint type-check test run docker-build docker-run clean

# Installation
install:
	pip install -r requirements.txt

dev-install: install
	pip install pytest pytest-cov black

# Development
lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy app

# Testing
test:
	python -m pytest

coverage:
	python -m pytest --cov=app tests/

# Running
run:
	uvicorn app.api.main:app --reload

# Docker
docker-build:
	docker build -t agent-framework .

docker-run:
	docker run -p 8000:8000 --env-file .env agent-framework

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Cleanup
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help
help:
	@echo "Available commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with ruff"
	@echo "  make type-check     - Run mypy type checking"
	@echo "  make test           - Run tests"
	@echo "  make coverage       - Run tests with coverage report"
	@echo "  make run            - Run development server"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make clean          - Clean up temporary files" 