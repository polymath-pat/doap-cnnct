# Variables
APP_NAME := cnnct
COMPOSE  := podman-compose
VENV     := venv
PYTHON   := $(VENV)/bin/python3
PIP      := $(VENV)/bin/pip3

.PHONY: help install build up down test-e2e test-all fix-mac-security clean

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@touch $(VENV)/bin/activate

install: $(VENV)/bin/activate ## Create venv and install dependencies

fix-mac-security: ## Remove macOS quarantine from downloaded drivers
	@echo "🔓 Removing macOS quarantine flags from drivers..."
	-find ~/.wdm/drivers -name "chromedriver" -exec xattr -d com.apple.quarantine {} + 2>/dev/null || true

build: ## Build images
	$(COMPOSE) build --no-cache

up: ## Start stack
	$(COMPOSE) up -d

down: ## Stop stack
	$(COMPOSE) down

test-e2e: up install fix-mac-security ## Run E2E tests (includes security fix)
	@echo "🚀 Running E2E Tests..."
	@sleep 7
	$(PYTHON) tests/e2e_test.py

test-all: test-e2e ## Run all tests
	@echo "✅ All tests passed!"

clean: down
	rm -rf $(VENV)
	podman system prune -f