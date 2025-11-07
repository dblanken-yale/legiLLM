#!/bin/bash
# LegiScan Pipeline Runner - Convenience wrapper for Docker operations

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
}

# Check if containers are running
check_containers() {
    if ! docker-compose ps | grep -q "Up"; then
        warning "Containers not running. Starting..."
        docker-compose up -d
        sleep 2
    fi
}

# Show usage
usage() {
    cat << EOF
${BLUE}LegiScan Pipeline Runner${NC}

${GREEN}Usage:${NC}
    ./run.sh <command> [options]

${GREEN}Pipeline Commands:${NC}
    fetch           Fetch bills from LegiScan
    filter          Run filter pass
    analyze         Run analysis pass
    run             Run full pipeline (fetch → filter → analyze)

    test            Run pipeline in test mode (5 bills)
    test-filter     Run filter pass in test mode
    test-analyze    Run analysis pass in test mode

${GREEN}Multi-State Commands:${NC}
    fetch-multi     Fetch bills from CT, NY, CA, TX, FL
    filter-multi    Filter all fetched states
    run-multi       Run full pipeline for multiple states

${GREEN}Docker Commands:${NC}
    start           Start Docker containers
    stop            Stop Docker containers
    restart         Restart Docker containers
    shell           Open bash shell in container
    logs            Show container logs
    status          Show container status

${GREEN}Data Commands:${NC}
    results         Show analysis results summary
    view            View detailed analysis results
    clean           Clean all data files
    clean-cache     Clean API cache

${GREEN}LegiUI Commands:${NC}
    ui              Start LegiUI dashboard
    ui-build        Build LegiUI for production

${GREEN}Utility Commands:${NC}
    check           Check configuration and API connectivity
    help            Show this help message

${GREEN}Examples:${NC}
    ./run.sh fetch                  # Fetch bills from LegiScan
    ./run.sh filter                 # Run filter pass
    ./run.sh analyze                # Run analysis pass
    ./run.sh run                    # Run complete pipeline
    ./run.sh test                   # Quick test with 5 bills
    ./run.sh shell                  # Open container shell
    ./run.sh results                # View results summary
    ./run.sh ui                     # Start dashboard

EOF
}

# Main commands
cmd_fetch() {
    check_docker
    check_containers
    info "Fetching bills from LegiScan..."
    docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py
    success "Bills fetched to data/raw/"
}

cmd_filter() {
    check_docker
    check_containers
    info "Running filter pass..."
    docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
    success "Filter results saved to data/filtered/"
}

cmd_analyze() {
    check_docker
    check_containers
    info "Running analysis pass..."
    docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
    success "Analysis results saved to data/analyzed/"
}

cmd_run() {
    info "Running full pipeline..."
    cmd_fetch
    cmd_filter
    cmd_analyze
    success "✓✓✓ Full pipeline complete!"
    echo ""
    cmd_results
}

cmd_test() {
    check_docker
    check_containers
    info "Running pipeline in TEST MODE (5 bills)..."
    docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
    docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
    success "Test pipeline complete!"
    cmd_results
}

cmd_test_filter() {
    check_docker
    check_containers
    info "Running filter pass in TEST MODE..."
    docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
    success "Test filter complete!"
}

cmd_test_analyze() {
    check_docker
    check_containers
    info "Running analysis pass in TEST MODE..."
    docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
    success "Test analysis complete!"
}

cmd_fetch_multi() {
    check_docker
    check_containers
    info "Fetching bills from multiple states (CT, NY, CA, TX, FL)..."
    for state in CT NY CA TX FL; do
        info "Fetching $state..."
        docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py --state "$state"
    done
    success "All states fetched!"
}

cmd_filter_multi() {
    check_docker
    check_containers
    info "Filtering all states..."
    docker-compose exec legiscan-pipeline bash -c '
        cd scripts
        for file in ../data/raw/*_bills_*.json; do
            basename=$(basename "$file" .json)
            echo "Filtering $basename..."
            python run_filter_pass.py "$basename"
        done
    '
    success "All states filtered!"
}

cmd_run_multi() {
    info "Running full pipeline for multiple states..."
    cmd_fetch_multi
    cmd_filter_multi
    cmd_analyze
    success "✓✓✓ Multi-state pipeline complete!"
    cmd_results
}

cmd_start() {
    check_docker
    info "Starting containers..."
    docker-compose up -d
    success "Containers started"
}

cmd_stop() {
    info "Stopping containers..."
    docker-compose down
    success "Containers stopped"
}

cmd_restart() {
    info "Restarting containers..."
    docker-compose restart
    success "Containers restarted"
}

cmd_shell() {
    check_docker
    check_containers
    info "Opening shell in container..."
    docker-compose exec legiscan-pipeline bash
}

cmd_logs() {
    check_docker
    info "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f --tail=50 legiscan-pipeline
}

cmd_status() {
    check_docker
    info "Container status:"
    docker-compose ps
}

cmd_results() {
    check_docker
    check_containers
    info "Analysis Results Summary:"
    docker-compose exec legiscan-pipeline python -c "
import json, sys
from pathlib import Path

analyzed_dir = Path('data/analyzed')
if not analyzed_dir.exists():
    print('No analysis results found')
    sys.exit(0)

files = list(analyzed_dir.glob('*_relevant.json'))
if not files:
    print('No relevant bills found')
    sys.exit(0)

total = 0
for f in files:
    with open(f) as fh:
        bills = json.load(fh)
        count = len(bills)
        total += count
        print(f'{f.name}: {count} relevant bills')

print(f'\nTotal: {total} relevant bills across all files')
" || warning "No results yet. Run: ./run.sh run"
}

cmd_view() {
    check_docker
    check_containers
    docker-compose exec legiscan-pipeline python -c "
import json
from pathlib import Path

f = Path('data/analyzed/analysis_results_relevant.json')
if not f.exists():
    print('No analysis results found. Run: ./run.sh analyze')
    exit(1)

with open(f) as fh:
    bills = json.load(fh)
    print(f'Total relevant bills: {len(bills)}\n')

    if bills:
        print('First bill:')
        bill = bills[0]
        print(f'  Number: {bill[\"bill\"][\"bill_number\"]}')
        print(f'  Title: {bill[\"bill\"][\"title\"][:80]}...')
        print(f'  Categories: {bill[\"analysis\"][\"categories\"]}')
        print(f'  Status: {bill[\"analysis\"].get(\"bill_status\", \"Unknown\")}')
        print(f'  Summary: {bill[\"analysis\"].get(\"summary\", \"N/A\")[:100]}...')
"
}

cmd_clean() {
    warning "This will delete all data files (raw, filtered, analyzed)!"
    echo -n "Continue? (y/N) "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        check_docker
        check_containers
        info "Cleaning data directories..."
        docker-compose exec legiscan-pipeline bash -c "rm -rf data/raw/* data/filtered/* data/analyzed/*"
        success "Data cleaned"
    else
        info "Cancelled"
    fi
}

cmd_clean_cache() {
    check_docker
    check_containers
    info "Cleaning cache..."
    docker-compose exec legiscan-pipeline bash -c "rm -rf data/cache/legiscan_cache/*"
    success "Cache cleaned"
}

cmd_ui() {
    info "Starting LegiUI dashboard..."
    cd legiUI

    # Install if needed
    if [ ! -d "node_modules" ]; then
        info "Installing dependencies..."
        npm install
    fi

    # Load data
    info "Loading analysis data..."
    npm run load-data

    # Start dev server
    info "Starting development server..."
    success "UI will open at http://localhost:5173"
    npm run dev
}

cmd_ui_build() {
    info "Building LegiUI for production..."
    cd legiUI
    npm install
    npm run load-data
    npm run build
    success "Build complete: legiUI/dist/"
}

cmd_check() {
    check_docker
    check_containers

    info "Checking environment configuration..."
    docker-compose exec legiscan-pipeline python -c "
import os, sys

errors = []
warnings = []

# Check LegiScan
if not os.getenv('LEGISCAN_API_KEY'):
    errors.append('LEGISCAN_API_KEY not set')

# Check LLM provider
provider = os.getenv('LLM_PROVIDER', 'portkey')
print(f'LLM Provider: {provider}')

if provider == 'portkey':
    if not os.getenv('PORTKEY_API_KEY'):
        errors.append('PORTKEY_API_KEY not set')
elif provider == 'azure':
    if not os.getenv('AZURE_OPENAI_API_KEY'):
        errors.append('AZURE_OPENAI_API_KEY not set')
    if not os.getenv('AZURE_OPENAI_ENDPOINT'):
        errors.append('AZURE_OPENAI_ENDPOINT not set')
    if not os.getenv('AZURE_OPENAI_DEPLOYMENT'):
        errors.append('AZURE_OPENAI_DEPLOYMENT not set')
elif provider == 'ollama':
    print('Ollama configuration detected')
    base_url = os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1')
    print(f'Base URL: {base_url}')

if errors:
    print('\n✗ Configuration errors:')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('\n✓ Environment configured correctly')
"

    info "Testing API connectivity..."
    docker-compose exec legiscan-pipeline python -c "
import os, requests

# Test LegiScan
api_key = os.getenv('LEGISCAN_API_KEY')
if api_key:
    try:
        r = requests.get(f'https://api.legiscan.com/?key={api_key}&op=getSessionList&state=CT', timeout=10)
        if r.status_code == 200:
            print('✓ LegiScan API working')
        else:
            print(f'✗ LegiScan API error: {r.status_code}')
    except Exception as e:
        print(f'✗ LegiScan API error: {e}')
"

    success "Configuration check complete"
}

# Main script
case "${1:-help}" in
    fetch)
        cmd_fetch
        ;;
    filter)
        cmd_filter
        ;;
    analyze)
        cmd_analyze
        ;;
    run)
        cmd_run
        ;;
    test)
        cmd_test
        ;;
    test-filter)
        cmd_test_filter
        ;;
    test-analyze)
        cmd_test_analyze
        ;;
    fetch-multi)
        cmd_fetch_multi
        ;;
    filter-multi)
        cmd_filter_multi
        ;;
    run-multi)
        cmd_run_multi
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    shell)
        cmd_shell
        ;;
    logs)
        cmd_logs
        ;;
    status)
        cmd_status
        ;;
    results)
        cmd_results
        ;;
    view)
        cmd_view
        ;;
    clean)
        cmd_clean
        ;;
    clean-cache)
        cmd_clean_cache
        ;;
    ui)
        cmd_ui
        ;;
    ui-build)
        cmd_ui_build
        ;;
    check)
        cmd_check
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
