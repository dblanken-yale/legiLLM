# LegiScan Bill Analysis Pipeline - Makefile
# Convenient commands for running the pipeline in Docker

.PHONY: help build up down restart logs shell fetch filter analyze run test clean clean-data clean-all status

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)LegiScan Pipeline - Docker Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Management

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

up: ## Start containers in background
	@echo "$(BLUE)Starting containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"

down: ## Stop and remove containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

restart: ## Restart containers
	@echo "$(BLUE)Restarting containers...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Containers restarted$(NC)"

logs: ## Show container logs (follow mode)
	docker-compose logs -f legiscan-pipeline

shell: ## Open bash shell in container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	docker-compose exec legiscan-pipeline bash

status: ## Show container status
	@echo "$(BLUE)Container status:$(NC)"
	@docker-compose ps

##@ Pipeline Operations

fetch: ## Fetch bills from LegiScan (default: CT 2025)
	@echo "$(BLUE)Fetching bills from LegiScan...$(NC)"
	docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py
	@echo "$(GREEN)✓ Bills fetched$(NC)"
	@echo "Results in: data/raw/"

filter: ## Run filter pass on bills
	@echo "$(BLUE)Running filter pass...$(NC)"
	docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
	@echo "$(GREEN)✓ Filter pass complete$(NC)"
	@echo "Results in: data/filtered/"

analyze: ## Run analysis pass on filtered bills
	@echo "$(BLUE)Running analysis pass...$(NC)"
	docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
	@echo "$(GREEN)✓ Analysis pass complete$(NC)"
	@echo "Results in: data/analyzed/"

direct-analyze: ## Run direct analysis on pre-filtered data (requires FILTER_FILE variable)
	@if [ -z "$(FILTER_FILE)" ]; then \
		echo "$(RED)Error: FILTER_FILE not set$(NC)"; \
		echo "Usage: make direct-analyze FILTER_FILE=../data/filtered/filter_results_ct_bills_2025.json"; \
		exit 1; \
	fi
	@echo "$(BLUE)Running direct analysis on $(FILTER_FILE)...$(NC)"
	docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_direct_analysis.py $(FILTER_FILE)"
	@echo "$(GREEN)✓ Direct analysis complete$(NC)"

run: fetch filter analyze ## Run full pipeline (fetch → filter → analyze)
	@echo "$(GREEN)✓✓✓ Full pipeline complete!$(NC)"
	@echo "View results in: data/analyzed/"

##@ Testing

test: ## Run pipeline in test mode (5 bills only)
	@echo "$(BLUE)Running pipeline in TEST MODE (5 bills)...$(NC)"
	@echo "Setting TEST_MODE=true..."
	docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
	@echo "$(BLUE)Running analysis pass...$(NC)"
	docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
	@echo "$(GREEN)✓ Test pipeline complete$(NC)"

test-fetch: ## Fetch bills (test mode doesn't apply to fetch)
	@echo "$(BLUE)Fetching bills...$(NC)"
	docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py
	@echo "$(GREEN)✓ Bills fetched$(NC)"

test-filter: ## Run filter pass in test mode (5 bills)
	@echo "$(BLUE)Running filter pass (TEST MODE - 5 bills)...$(NC)"
	docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
	@echo "$(GREEN)✓ Test filter complete$(NC)"

test-analyze: ## Run analysis pass in test mode
	@echo "$(BLUE)Running analysis pass (TEST MODE)...$(NC)"
	docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
	@echo "$(GREEN)✓ Test analysis complete$(NC)"

##@ Data Management

results: ## Show analysis results summary
	@echo "$(BLUE)Analysis Results Summary:$(NC)"
	@docker-compose exec legiscan-pipeline python -c "\
import json, os, sys; \
from pathlib import Path; \
analyzed_dir = Path('data/analyzed'); \
if not analyzed_dir.exists(): \
    print('No analysis results found'); \
    sys.exit(0); \
files = list(analyzed_dir.glob('*_relevant.json')); \
if not files: \
    print('No relevant bills found'); \
    sys.exit(0); \
for f in files: \
    with open(f) as fh: \
        bills = json.load(fh); \
        print(f'{f.name}: {len(bills)} relevant bills'); \
" || echo "No results yet"

view-results: ## View detailed analysis results
	@docker-compose exec legiscan-pipeline python -c "\
import json; \
from pathlib import Path; \
f = Path('data/analyzed/analysis_results_relevant.json'); \
if f.exists(): \
    with open(f) as fh: \
        bills = json.load(fh); \
        print(f'Total relevant bills: {len(bills)}'); \
        if bills: \
            print('\nFirst bill:'); \
            print(f'  Number: {bills[0][\"bill\"][\"bill_number\"]}'); \
            print(f'  Title: {bills[0][\"bill\"][\"title\"][:80]}...'); \
            print(f'  Categories: {bills[0][\"analysis\"][\"categories\"]}'); \
            print(f'  Status: {bills[0][\"analysis\"].get(\"bill_status\", \"Unknown\")}'); \
else: \
    print('No analysis results found. Run: make analyze'); \
"

clean-data: ## Remove all data files (raw, filtered, analyzed)
	@echo "$(YELLOW)⚠ This will delete all data files!$(NC)"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	@echo "$(BLUE)Cleaning data directories...$(NC)"
	docker-compose exec legiscan-pipeline bash -c "rm -rf data/raw/* data/filtered/* data/analyzed/*"
	@echo "$(GREEN)✓ Data cleaned$(NC)"

clean-cache: ## Remove cached LegiScan API responses
	@echo "$(BLUE)Cleaning cache...$(NC)"
	docker-compose exec legiscan-pipeline bash -c "rm -rf data/cache/legiscan_cache/*"
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

clean: down ## Stop containers and clean build cache
	@echo "$(BLUE)Cleaning Docker cache...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean clean-data clean-cache ## Remove everything (containers, data, cache)
	@echo "$(RED)⚠ This will delete EVERYTHING!$(NC)"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	@echo "$(BLUE)Cleaning all data and containers...$(NC)"
	docker-compose down -v
	rm -rf data/raw/* data/filtered/* data/analyzed/* data/cache/*
	@echo "$(GREEN)✓ Everything cleaned$(NC)"

##@ LegiUI

ui-install: ## Install LegiUI dependencies
	@echo "$(BLUE)Installing LegiUI dependencies...$(NC)"
	cd legiUI && npm install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

ui-load: ## Load data into LegiUI from analysis results
	@echo "$(BLUE)Loading data into LegiUI...$(NC)"
	cd legiUI && npm run load-data
	@echo "$(GREEN)✓ Data loaded$(NC)"

ui-dev: ## Start LegiUI development server
	@echo "$(BLUE)Starting LegiUI development server...$(NC)"
	cd legiUI && npm run dev

ui-build: ## Build LegiUI for production
	@echo "$(BLUE)Building LegiUI...$(NC)"
	cd legiUI && npm run build
	@echo "$(GREEN)✓ Build complete: legiUI/dist/$(NC)"

ui: ui-install ui-load ui-dev ## Install, load data, and start LegiUI

##@ Multi-State Processing

fetch-multi: ## Fetch bills from multiple states (CT, NY, CA, TX, FL)
	@echo "$(BLUE)Fetching bills from multiple states...$(NC)"
	@for state in CT NY CA TX FL; do \
		echo "$(BLUE)Fetching $$state...$(NC)"; \
		docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py --state $$state; \
	done
	@echo "$(GREEN)✓ All states fetched$(NC)"

filter-multi: ## Run filter pass on all states in data/raw/
	@echo "$(BLUE)Filtering all states...$(NC)"
	docker-compose exec legiscan-pipeline bash -c '\
		cd scripts && \
		for file in ../data/raw/*_bills_*.json; do \
			basename=$$(basename $$file .json); \
			echo "Filtering $$basename..."; \
			python run_filter_pass.py $$basename; \
		done \
	'
	@echo "$(GREEN)✓ All states filtered$(NC)"

run-multi: fetch-multi filter-multi analyze ## Run full pipeline for multiple states

##@ Utilities

check-env: ## Check if required environment variables are set
	@echo "$(BLUE)Checking environment configuration...$(NC)"
	@docker-compose exec legiscan-pipeline python -c "\
import os, sys; \
errors = []; \
if not os.getenv('LEGISCAN_API_KEY'): errors.append('LEGISCAN_API_KEY not set'); \
provider = os.getenv('LLM_PROVIDER', 'portkey'); \
if provider == 'portkey' and not os.getenv('PORTKEY_API_KEY'): \
    errors.append('PORTKEY_API_KEY not set'); \
elif provider == 'azure': \
    if not os.getenv('AZURE_OPENAI_API_KEY'): errors.append('AZURE_OPENAI_API_KEY not set'); \
    if not os.getenv('AZURE_OPENAI_ENDPOINT'): errors.append('AZURE_OPENAI_ENDPOINT not set'); \
    if not os.getenv('AZURE_OPENAI_DEPLOYMENT'): errors.append('AZURE_OPENAI_DEPLOYMENT not set'); \
if errors: \
    print('$(RED)✗ Configuration errors:$(NC)'); \
    for e in errors: print(f'  - {e}'); \
    sys.exit(1); \
else: \
    print('$(GREEN)✓ Environment configured correctly$(NC)'); \
    print(f'  LLM Provider: {provider}'); \
"

test-api: ## Test API connectivity (LLM and LegiScan)
	@echo "$(BLUE)Testing API connectivity...$(NC)"
	@echo "Testing LegiScan API..."
	@docker-compose exec legiscan-pipeline python -c "\
import os, requests; \
api_key = os.getenv('LEGISCAN_API_KEY'); \
if not api_key: \
    print('$(RED)✗ LEGISCAN_API_KEY not set$(NC)'); \
else: \
    try: \
        r = requests.get(f'https://api.legiscan.com/?key={api_key}&op=getSessionList&state=CT'); \
        if r.status_code == 200: print('$(GREEN)✓ LegiScan API working$(NC)'); \
        else: print(f'$(RED)✗ LegiScan API error: {r.status_code}$(NC)'); \
    except Exception as e: \
        print(f'$(RED)✗ LegiScan API error: {e}$(NC)'); \
"
	@echo "Testing LLM API..."
	@docker-compose exec legiscan-pipeline python scripts/test_llm_connection.py 2>/dev/null || echo "$(YELLOW)⚠ Create scripts/test_llm_connection.py for LLM testing$(NC)"

show-config: ## Show current configuration
	@echo "$(BLUE)Current Configuration:$(NC)"
	@docker-compose exec legiscan-pipeline python -c "\
import os, json; \
from pathlib import Path; \
print(f'LLM Provider: {os.getenv(\"LLM_PROVIDER\", \"portkey\")}'); \
print(f'LLM Model: {os.getenv(\"LLM_MODEL\", \"gpt-4o-mini\")}'); \
print(f'Test Mode: {os.getenv(\"TEST_MODE\", \"false\")}'); \
print(f'Test Count: {os.getenv(\"TEST_COUNT\", \"5\")}'); \
config_file = Path('config.json'); \
if config_file.exists(): \
    with open(config_file) as f: \
        config = json.load(f); \
        print(f'Batch Size: {config.get(\"filter_pass\", {}).get(\"batch_size\", 50)}'); \
        print(f'Cache Enabled: {config.get(\"legiscan\", {}).get(\"cache_enabled\", True)}'); \
"

watch: ## Watch pipeline logs in real-time
	@echo "$(BLUE)Watching logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs -f --tail=50 legiscan-pipeline

##@ Quick Commands

quick-test: up test-fetch test-filter test-analyze results ## Quick test of full pipeline (5 bills)
	@echo "$(GREEN)✓✓✓ Quick test complete!$(NC)"

quick-run: up fetch filter analyze results ## Quick full pipeline run
	@echo "$(GREEN)✓✓✓ Pipeline complete!$(NC)"

quick-ui: ui-load ui-dev ## Quick start LegiUI with existing data
	@echo "$(GREEN)✓ UI ready$(NC)"

##@ Docker Shortcuts

exec: ## Execute command in container (usage: make exec CMD="ls -la")
	@if [ -z "$(CMD)" ]; then \
		echo "$(RED)Error: CMD not set$(NC)"; \
		echo "Usage: make exec CMD=\"your command here\""; \
		exit 1; \
	fi
	docker-compose exec legiscan-pipeline $(CMD)

run-script: ## Run a Python script in container (usage: make run-script SCRIPT="scripts/test.py")
	@if [ -z "$(SCRIPT)" ]; then \
		echo "$(RED)Error: SCRIPT not set$(NC)"; \
		echo "Usage: make run-script SCRIPT=\"scripts/your_script.py\""; \
		exit 1; \
	fi
	docker-compose exec legiscan-pipeline python $(SCRIPT)

##@ Information

version: ## Show versions
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@docker-compose exec legiscan-pipeline python --version 2>/dev/null || echo "Container not running"

size: ## Show data directory sizes
	@echo "$(BLUE)Data Directory Sizes:$(NC)"
	@du -sh data/raw 2>/dev/null || echo "  raw/: empty"
	@du -sh data/filtered 2>/dev/null || echo "  filtered/: empty"
	@du -sh data/analyzed 2>/dev/null || echo "  analyzed/: empty"
	@du -sh data/cache 2>/dev/null || echo "  cache/: empty"
