# Docker Setup for LegiScan Bill Analysis Pipeline

This guide helps you run the LegiScan bill analysis pipeline using Docker for easy testing and development.

## Prerequisites

- Docker and Docker Compose installed
- LegiScan API key
- Portkey API key (for AI analysis)

## Quick Start

### 1. Configure Environment Variables

Add your LegiScan API key to the `.env` file:

```bash
# .env file should contain:
PORTKEY_API_KEY=your_portkey_api_key_here
LEGISCAN_API_KEY=your_legiscan_api_key_here
```

### 2. Build and Start

```bash
# Build the Docker image
./docker-run.sh build

# Start the container
./docker-run.sh up
```

### 3. Run Pipeline Commands

The helper script provides easy access to all pipeline commands:

```bash
# Fetch bills from LegiScan API
./docker-run.sh fetch

# Run filter pass
./docker-run.sh filter ct_bills_2025.json

# Run analysis pass
./docker-run.sh analyze

# Run in test mode (5 bills only)
./docker-run.sh test

# Access shell for manual commands
./docker-run.sh shell
```

## Docker Helper Script Commands

The `docker-run.sh` script provides these commands:

| Command | Description |
|---------|-------------|
| `build` | Build the Docker image |
| `up` | Start the container in detached mode |
| `down` | Stop and remove the container |
| `shell` | Open interactive bash shell in container |
| `fetch` | Fetch bills from LegiScan API (Connecticut 2025) |
| `filter [file]` | Run filter pass on specified file |
| `analyze` | Run analysis pass on filtered results |
| `direct [file]` | Run direct analysis on pre-filtered results |
| `test` | Run analysis in test mode (5 bills) |
| `logs` | Show container logs (follows) |
| `restart` | Restart the container |

## Manual Docker Commands

If you prefer using Docker Compose directly:

```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# Access shell
docker-compose exec legiscan-pipeline /bin/bash

# Run commands inside container
docker-compose exec legiscan-pipeline bash -c "cd scripts && python fetch_legiscan_bills.py"

# Stop container
docker-compose down

# View logs
docker-compose logs -f
```

## Development Mode

The `docker-compose.yml` is configured for development with:

- **Volume mounts**: Local `src/`, `scripts/`, and `prompts/` directories are mounted, so changes are reflected immediately
- **Data persistence**: `./data` directory is mounted for persistent storage
- **Interactive mode**: Container stays running for easy shell access

To disable development mounts (for production-like testing), comment out these lines in `docker-compose.yml`:

```yaml
# volumes:
#   - ./src:/app/src
#   - ./scripts:/app/scripts
#   - ./prompts:/app/prompts
```

## Working Inside the Container

Once inside the container shell (`./docker-run.sh shell`):

```bash
# Navigate to scripts directory
cd scripts

# Fetch bills
python fetch_legiscan_bills.py

# Run filter pass
python run_filter_pass.py ct_bills_2025.json

# Run analysis pass
python run_analysis_pass.py

# Test mode
TEST_MODE=true TEST_COUNT=5 python run_analysis_pass.py

# Check data
ls -la ../data/raw/
ls -la ../data/filtered/
ls -la ../data/analyzed/
```

## Data Persistence

All data is stored in the `./data` directory on your host machine:

```
data/
├── raw/              # Raw LegiScan bill data
├── filtered/         # Filter pass results
├── analyzed/         # Analysis pass results
└── cache/            # LegiScan API cache
    └── legiscan_cache/
```

This data persists even when the container is stopped or removed.

## Troubleshooting

### Container won't start
```bash
# Check logs
./docker-run.sh logs

# Rebuild image
./docker-run.sh down
./docker-run.sh build
./docker-run.sh up
```

### API keys not working
```bash
# Verify .env file exists and has correct keys
cat .env

# Restart container to reload environment
./docker-run.sh restart
```

### Permission issues with data directory
```bash
# Fix permissions on host
sudo chown -R $USER:$USER data/
```

### Clear cache and start fresh
```bash
# Stop container
./docker-run.sh down

# Clear data
rm -rf data/cache/*
rm -rf data/analyzed/*
rm -rf data/filtered/*

# Restart
./docker-run.sh up
```

## Test Mode

Test mode processes only 5 bills for quick testing:

```bash
# Using helper script
./docker-run.sh test

# Or manually
docker-compose exec -e TEST_MODE=true -e TEST_COUNT=5 legiscan-pipeline \
    bash -c "cd scripts && python run_analysis_pass.py"
```

## Production Deployment

For production deployment (Azure, AWS, etc.):

1. Build production image without development mounts
2. Use environment variables from Azure Key Vault or AWS Secrets Manager
3. Use Azure Blob Storage or S3 instead of local volumes
4. See `infrastructure/` directory for deployment templates

## Next Steps

- See `CLAUDE.md` for detailed pipeline documentation
- See `docs/` for architecture and configuration details
- Check `config.json` for pipeline settings
