# Quick Start Guide - Docker Testing

Get up and running with the LegiScan pipeline in Docker in under 5 minutes.

## Step 1: Add LegiScan API Key

Edit `.env` file and add your LegiScan API key:

```bash
PORTKEY_API_KEY=dcIjx3/Hsz30nfARrh/kK3RGfm8l
LEGISCAN_API_KEY=your_legiscan_api_key_here
```

## Step 2: Build and Start

```bash
./docker-run.sh build
./docker-run.sh up
```

## Step 3: Run a Test

Test with just 5 bills to verify everything works:

```bash
./docker-run.sh test
```

## Step 4: Run Full Pipeline

```bash
# 1. Fetch bills (if you don't have data/raw/ct_bills_2025.json)
./docker-run.sh fetch

# 2. Filter bills (fast, metadata only)
./docker-run.sh filter ct_bills_2025.json

# 3. Analyze relevant bills (full text analysis)
./docker-run.sh analyze
```

## Check Results

```bash
# Access the container
./docker-run.sh shell

# Inside container, check results
cd data
ls -la filtered/    # Filter pass results
ls -la analyzed/    # Analysis pass results
cat analyzed/analysis_results_relevant.json | head -50
exit
```

## Common Commands

```bash
./docker-run.sh shell       # Interactive shell
./docker-run.sh logs        # View logs
./docker-run.sh restart     # Restart container
./docker-run.sh down        # Stop container
```

## Results Location

All results are saved to your local `./data` directory:

- `data/raw/ct_bills_2025.json` - Fetched bills from LegiScan
- `data/filtered/filter_results_*.json` - Bills identified as potentially relevant
- `data/analyzed/analysis_results_relevant.json` - Categorized relevant bills
- `data/cache/legiscan_cache/` - Cached LegiScan API responses

## Need Help?

- Full Docker guide: `DOCKER.md`
- Project documentation: `CLAUDE.md`
- Pipeline architecture: `docs/ARCHITECTURE.md`

## Troubleshooting

**Container won't start?**
```bash
./docker-run.sh logs
```

**Need to start fresh?**
```bash
./docker-run.sh down
./docker-run.sh build
./docker-run.sh up
```

**API issues?**
- Check that both API keys are in `.env`
- Verify LegiScan API key is valid
- Check rate limits (use `api_delay` in `config.json`)
