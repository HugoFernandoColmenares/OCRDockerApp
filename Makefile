# Inventory OCR Scanner - Makefile
# Simplifies common development and deployment tasks

.PHONY: help install run test build clean logs stop restart

# Default target
help:
	@echo "Inventory OCR Scanner - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install Python dependencies"
	@echo "  make run        - Run application locally"
	@echo "  make test       - Run tests"
	@echo "  make dev        - Run in development mode"
	@echo ""
	@echo "Docker:"
	@echo "  make build      - Build Docker containers"
	@echo "  make up         - Start Docker containers"
	@echo "  make down       - Stop Docker containers"
	@echo "  make restart    - Restart Docker containers"
	@echo "  make logs       - View container logs"
	@echo "  make clean      - Clean up Docker resources"
	@echo ""
	@echo "Utilities:"
	@echo "  make format     - Format code with black"
	@echo "  make lint       - Run linting with flake8"
	@echo "  make security   - Run security checks"
	@echo "  make setup      - Initial setup"

# Development commands
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

run:
	@echo "🚀 Running application..."
	python app.py

test:
	@echo "🧪 Running Docker smoke test..."
	docker compose run --rm --no-deps ocr-app python tests/smoke_test.py

dev:
	@echo "🔧 Running in development mode..."
	FLASK_ENV=development python app.py

# Docker commands
build:
	@echo "🔨 Building Docker containers..."
	docker-compose build

up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d

down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

restart: down up
	@echo "🔄 Restarting Docker containers..."

logs:
	@echo "📋 Viewing container logs..."
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down --rmi all --volumes
	docker system prune -f

# Code quality
format:
	@echo "🎨 Formatting code..."
	black *.py
	black static/

lint:
	@echo "🔍 Running linting checks..."
	flake8 *.py --max-line-length=88

security:
	@echo "🔒 Running security checks..."
	pip install bandit safety
	bandit -r . -f json
	safety check

# Setup
setup:
	@echo "⚙️  Setting up development environment..."
	mkdir -p uploads results logs
	chmod +x deploy.sh
	@echo "✅ Setup complete!"

# Deployment
deploy:
	@echo "🚀 Deploying application..."
	./deploy.sh

# Quick start
start: build up
	@echo "🎉 Application is starting..."
	@echo "   Main app: http://localhost:8000"
	@echo "   Via Nginx: http://localhost"

# Stop everything
stop:
	@echo "🛑 Stopping all services..."
	docker-compose down
	pkill -f "python app.py" || true

# Development setup
dev-setup: install setup
	@echo "🛠️  Development environment ready!"
	@echo "   Run 'make dev' to start development server"
	@echo "   Run 'make test' to run tests"

# Production deployment
prod-deploy: build up
	@echo "🏭 Production deployment complete!"
	@echo "   Monitor with: make logs"
	@echo "   Health check: curl http://localhost:8000/api/health"