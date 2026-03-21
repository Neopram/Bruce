# =============================================================================
# BruceWayneV1 - Makefile
# Developer-friendly commands for common tasks
# =============================================================================

.PHONY: help install dev test lint format docker-build docker-up docker-down clean \
	train-knowledge train-ppo train-lstm train-rlhf train-all fetch-data evaluate

# Default target
help: ## Show this help message
	@echo "BruceWayneV1 - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python dependencies
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install black flake8 isort pytest pytest-cov pytest-asyncio bandit

install-frontend: ## Install Node.js dependencies
	npm ci

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start backend and frontend dev servers
	@echo "Starting backend and frontend..."
	@make dev-backend &
	@make dev-frontend &
	@wait

dev-backend: ## Start backend dev server
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend dev server
	npm run dev

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-backend test-frontend ## Run all tests

test-backend: ## Run Python tests with coverage
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

test-frontend: ## Run frontend tests
	npm test -- --passWithNoTests

test-watch: ## Run backend tests in watch mode
	pytest tests/ -v --watch

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Run Python linters
	black --check --diff .
	flake8 . --max-line-length=120 --exclude=node_modules,.next,__pycache__,venv,.venv
	isort --check-only --diff .

lint-frontend: ## Run frontend linters
	npx eslint . --ext .ts,.tsx,.js,.jsx --max-warnings 0

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

format: format-backend format-frontend ## Format all code

format-backend: ## Format Python code
	black .
	isort .

format-frontend: ## Format frontend code
	npx prettier --write "**/*.{ts,tsx,js,jsx,json,css,md}"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

security: ## Run security scans
	bandit -r . -x ./node_modules,./tests,./.next,./venv,./.venv --severity-level medium
	pip install safety && safety check -r requirements.txt

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-build: ## Build Docker images
	docker compose -f docker-compose.prod.yml build

docker-up: ## Start Docker services
	docker compose -f docker-compose.prod.yml up -d

docker-down: ## Stop Docker services
	docker compose -f docker-compose.prod.yml down

docker-logs: ## View Docker logs
	docker compose -f docker-compose.prod.yml logs -f

docker-ps: ## Show Docker service status
	docker compose -f docker-compose.prod.yml ps

docker-restart: ## Restart Docker services
	docker compose -f docker-compose.prod.yml restart

docker-clean: ## Remove Docker volumes and images
	docker compose -f docker-compose.prod.yml down -v --rmi local

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db-migrate: ## Run database migrations
	docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

db-shell: ## Open database shell
	docker compose -f docker-compose.prod.yml exec postgres psql -U bruce -d brucewayne

db-backup: ## Create database backup
	docker compose -f docker-compose.prod.yml exec -T postgres \
		pg_dump -U bruce brucewayne > backup_$$(date +%Y%m%d_%H%M%S).sql

# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

train-knowledge: ## Train shipping and crypto knowledge models
	python scripts/train_shipping.py
	python scripts/train_crypto.py

train-ppo: ## Train PPO reinforcement learning agent
	python scripts/train_ppo.py

train-lstm: ## Train LSTM time-series forecasting model
	python scripts/train_lstm.py

train-rlhf: ## Train RLHF reward model and fine-tune
	python scripts/train_rlhf.py

train-all: train-knowledge train-ppo train-lstm train-rlhf ## Run all training pipelines in sequence

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

fetch-data: ## Fetch latest market and shipping data
	python scripts/fetch_market_data.py
	python scripts/fetch_shipping_data.py

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

evaluate: ## Evaluate all trained models
	python scripts/evaluate_models.py

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .next node_modules/.cache
	rm -rf coverage.xml .coverage
	@echo "Cleaned generated files and caches."

# ---------------------------------------------------------------------------
# Model Downloads
# ---------------------------------------------------------------------------

download-models: ## Download all AI models locally
	python scripts/download_models.py --model all

download-models-api: ## Download API-only model stubs
	python scripts/download_models.py --api-only

# ---------------------------------------------------------------------------
# SSL & Data
# ---------------------------------------------------------------------------

generate-ssl: ## Generate self-signed SSL certificates
	bash scripts/generate_ssl.sh

connect-data: ## Test real data source connections
	python scripts/connect_real_data.py --test

# ---------------------------------------------------------------------------
# Full Setup
# ---------------------------------------------------------------------------

full-setup: install download-models-api fetch-data train-knowledge ## Complete project setup from scratch
