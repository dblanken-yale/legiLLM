#!/bin/bash
# Helper script for running LegiScan pipeline commands in Docker

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${BLUE}LegiScan Bill Analysis Pipeline - Docker Helper${NC}"
    echo ""
    echo "Usage: ./docker-run.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  build          Build the Docker image"
    echo "  up             Start the container"
    echo "  down           Stop the container"
    echo "  shell          Open a bash shell in the container"
    echo "  fetch          Fetch bills from LegiScan API"
    echo "  filter [file]  Run filter pass (default: ct_bills_2025.json)"
    echo "  analyze        Run analysis pass on filtered results"
    echo "  direct [file]  Run direct analysis on pre-filtered results"
    echo "  test           Run in test mode (5 bills)"
    echo "  logs           Show container logs"
    echo "  restart        Restart the container"
    echo ""
    echo "Examples:"
    echo "  ./docker-run.sh build"
    echo "  ./docker-run.sh up"
    echo "  ./docker-run.sh shell"
    echo "  ./docker-run.sh fetch"
    echo "  ./docker-run.sh filter ct_bills_2025.json"
    echo "  ./docker-run.sh analyze"
    echo "  ./docker-run.sh test"
    exit 1
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}Error: docker-compose or docker compose is not installed${NC}"
    exit 1
fi

# Use docker-compose or docker compose based on availability
DOCKER_COMPOSE="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

# Parse command
case "${1:-}" in
    build)
        echo -e "${GREEN}Building Docker image...${NC}"
        $DOCKER_COMPOSE build
        ;;

    up)
        echo -e "${GREEN}Starting container...${NC}"
        $DOCKER_COMPOSE up -d
        echo -e "${GREEN}Container started. Use './docker-run.sh shell' to access it.${NC}"
        ;;

    down)
        echo -e "${YELLOW}Stopping container...${NC}"
        $DOCKER_COMPOSE down
        ;;

    shell)
        echo -e "${GREEN}Opening shell in container...${NC}"
        $DOCKER_COMPOSE exec legiscan-pipeline /bin/bash
        ;;

    fetch)
        echo -e "${GREEN}Fetching bills from LegiScan API...${NC}"
        $DOCKER_COMPOSE exec legiscan-pipeline bash -c "cd scripts && python fetch_legiscan_bills.py"
        ;;

    filter)
        FILE="${2:-ct_bills_2025.json}"
        echo -e "${GREEN}Running filter pass on ${FILE}...${NC}"
        $DOCKER_COMPOSE exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py ${FILE}"
        ;;

    analyze)
        echo -e "${GREEN}Running analysis pass...${NC}"
        $DOCKER_COMPOSE exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
        ;;

    direct)
        if [ -z "${2}" ]; then
            echo -e "${YELLOW}Error: Please provide filter results file${NC}"
            echo "Example: ./docker-run.sh direct ../data/filtered/filter_results_ct_bills_2025.json"
            exit 1
        fi
        FILE="${2}"
        echo -e "${GREEN}Running direct analysis on ${FILE}...${NC}"
        $DOCKER_COMPOSE exec legiscan-pipeline bash -c "cd scripts && python run_direct_analysis.py ${FILE}"
        ;;

    test)
        echo -e "${GREEN}Running in TEST MODE (5 bills)...${NC}"
        $DOCKER_COMPOSE exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
        ;;

    logs)
        echo -e "${GREEN}Showing container logs...${NC}"
        $DOCKER_COMPOSE logs -f legiscan-pipeline
        ;;

    restart)
        echo -e "${YELLOW}Restarting container...${NC}"
        $DOCKER_COMPOSE restart legiscan-pipeline
        ;;

    *)
        usage
        ;;
esac
