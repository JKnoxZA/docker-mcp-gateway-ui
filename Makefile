.PHONY: help setup start stop restart build clean test lint format migrate seed logs

# Default target
help:
	@echo "MCP Docker Gateway - Development Commands"
	@echo ""
	@echo "Setup & Environment:"
	@echo "  setup         - Initial project setup"
	@echo "  start         - Start all services"
	@echo "  stop          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  build         - Build all Docker images"
	@echo "  clean         - Clean up containers and volumes"
	@echo ""
	@echo "Development:"
	@echo "  test          - Run all tests"
	@echo "  test-backend  - Run backend tests only"
	@echo "  test-frontend - Run frontend tests only"
	@echo "  lint          - Run linting for all projects"
	@echo "  format        - Format code for all projects"
	@echo ""
	@echo "Database:"
	@echo "  migrate       - Run database migrations"
	@echo "  migrate-reset - Reset database and run migrations"
	@echo "  seed          - Seed database with sample data"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs          - Show logs for all services"
	@echo "  logs-backend  - Show backend logs"
	@echo "  logs-frontend - Show frontend logs"

# Setup and Environment
setup:
	@echo "Setting up MCP Docker Gateway..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "Created backend/.env file"; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; echo "Created frontend/.env file"; fi
	@echo "Installing backend dependencies..."
	@cd backend && python -m pip install --upgrade pip && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Setup complete! Run 'make start' to start the application."

start:
	@echo "Starting MCP Docker Gateway..."
	@docker-compose up -d
	@echo "Services started. Frontend: http://localhost:3000, Backend: http://localhost:8000"

stop:
	@echo "Stopping all services..."
	@docker-compose down

restart: stop start

build:
	@echo "Building Docker images..."
	@docker-compose build

clean:
	@echo "Cleaning up containers and volumes..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f

# Development
test:
	@echo "Running all tests..."
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend:
	@echo "Running backend tests..."
	@cd backend && python -m pytest --cov=app --cov-report=term-missing

test-frontend:
	@echo "Running frontend tests..."
	@cd frontend && npm run test:coverage

lint:
	@echo "Running linting..."
	@cd backend && black --check . && isort --check-only . && mypy app/
	@cd frontend && npm run lint && npm run type-check

format:
	@echo "Formatting code..."
	@cd backend && black . && isort .
	@cd frontend && npm run lint:fix

# Database
migrate:
	@echo "Running database migrations..."
	@cd backend && alembic upgrade head

migrate-reset:
	@echo "Resetting database and running migrations..."
	@cd backend && alembic downgrade base && alembic upgrade head

seed:
	@echo "Seeding database with sample data..."
	@cd backend && python -m app.scripts.seed_data

# Monitoring
logs:
	@docker-compose logs -f

logs-backend:
	@docker-compose logs -f backend

logs-frontend:
	@docker-compose logs -f frontend

# Development shortcuts
dev-backend:
	@echo "Starting backend in development mode..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend in development mode..."
	@cd frontend && npm run dev

# Health checks
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Backend not responding"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: OK" || echo "Frontend: Not responding"

# Docker shortcuts
shell-backend:
	@docker-compose exec backend bash

shell-frontend:
	@docker-compose exec frontend sh

shell-db:
	@docker-compose exec postgres psql -U postgres -d mcp_gateway_db