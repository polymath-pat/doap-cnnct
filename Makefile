# Variables
COMPOSE = podman-compose

.PHONY: help dev build down logs clean shell-backend

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

check: ## Verify health of all services
	@echo "🔍 Checking Redis..."
	@$(COMPOSE) exec redis redis-cli ping | grep -q "PONG" && echo "✅ Redis is online" || echo "❌ Redis is offline"
	
	@echo "🔍 Checking Backend API..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/cnnct?target=doompatrol.io | grep -q "200" && echo "✅ Backend is responding" || echo "❌ Backend is failing"
	
	@echo "🔍 Checking Frontend UI..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200" && echo "✅ Frontend is serving" || echo "❌ Frontend is failing"

dev: ## Start stack and wait for health
	$(COMPOSE) up -d --build
	@echo "⏳ Waiting for services to initialize..."
	@sleep 5
	@make check
	@echo "🚀 App fully ready at http://localhost"

build: ## Rebuild all containers without starting them
	$(COMPOSE) build

down: ## Stop and remove all containers
	$(COMPOSE) down

logs: ## Follow logs from all containers
	@echo "Run $(COMPOSE) logs -f <COMPONENT>" 
	@echo "Where <COMPONENT> is one of backend, frontend or redis"

clean: ## Remove containers and delete volumes (wipes Redis data)
	$(COMPOSE) down -v
	@echo "🧹 Environment cleaned."

shell-backend: ## Jump into the running backend container for debugging
	$(COMPOSE) exec backend /bin/bash
