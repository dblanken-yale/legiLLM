# Convenience Commands for Docker Pipeline

Three easy ways to run the LegiScan pipeline in Docker without typing long commands.

## Quick Reference

| Method | Best For | Example |
|--------|----------|---------|
| **Makefile** | Unix/Mac developers | `make filter` |
| **run.sh** | Shell script users | `./run.sh filter` |
| **pipeline.py** | Python users | `python pipeline.py filter` |

All three methods provide the same functionality with slightly different interfaces.

---

## Method 1: Makefile (Recommended)

### Installation

No installation needed! Makefile is already in the project root.

### Usage

```bash
# Show all available commands
make help

# Common operations
make fetch          # Fetch bills from LegiScan
make filter         # Run filter pass
make analyze        # Run analysis pass
make run            # Run full pipeline (fetch → filter → analyze)

# Test mode (5 bills only)
make test           # Quick test of full pipeline
make test-filter    # Test filter pass only
make test-analyze   # Test analysis pass only

# View results
make results        # Show summary
make view-results   # Show detailed results

# Multi-state processing
make fetch-multi    # Fetch CT, NY, CA, TX, FL
make filter-multi   # Filter all states
make run-multi      # Full pipeline for all states

# Docker management
make up             # Start containers
make down           # Stop containers
make logs           # View logs
make shell          # Open shell in container

# LegiUI
make ui-load        # Load data into UI
make ui-dev         # Start UI dev server
make ui             # Load data and start UI

# Cleanup
make clean-data     # Remove data files
make clean-cache    # Remove API cache
```

### Examples

```bash
# Quick test to verify everything works
make up             # Start containers
make test           # Test with 5 bills
make results        # View results

# Full production run
make run            # Fetch → filter → analyze
make results        # View summary
make ui             # Start dashboard

# Process multiple states
make fetch-multi    # Fetch 5 states
make filter-multi   # Filter all
make analyze        # Analyze all
make results        # View combined results

# Direct analysis with pre-filtered data
make direct-analyze FILTER_FILE=../data/filtered/filter_results_alan_ct_bills_2025.json
```

---

## Method 2: run.sh Shell Script

### Installation

```bash
# Make executable (already done if you just created it)
chmod +x run.sh
```

### Usage

```bash
# Show all available commands
./run.sh help

# Common operations
./run.sh fetch          # Fetch bills
./run.sh filter         # Run filter pass
./run.sh analyze        # Run analysis pass
./run.sh run            # Full pipeline

# Test mode
./run.sh test           # Quick test (5 bills)
./run.sh test-filter    # Test filter only
./run.sh test-analyze   # Test analysis only

# View results
./run.sh results        # Show summary
./run.sh view           # Show detailed results

# Multi-state
./run.sh fetch-multi    # Fetch multiple states
./run.sh filter-multi   # Filter all states
./run.sh run-multi      # Full multi-state pipeline

# Docker management
./run.sh start          # Start containers
./run.sh stop           # Stop containers
./run.sh logs           # View logs
./run.sh shell          # Open shell

# LegiUI
./run.sh ui             # Load data and start UI
./run.sh ui-build       # Build for production

# Utilities
./run.sh check          # Check configuration
./run.sh clean          # Clean data
./run.sh clean-cache    # Clean API cache
```

### Examples

```bash
# First time setup
./run.sh start          # Start containers
./run.sh check          # Verify configuration
./run.sh test           # Quick test

# Regular workflow
./run.sh fetch          # Get bills
./run.sh filter         # Filter them
./run.sh analyze        # Analyze relevant ones
./run.sh results        # View summary

# Debugging
./run.sh logs           # Check logs
./run.sh shell          # Open container shell
./run.sh status         # Check container status
```

---

## Method 3: pipeline.py Python CLI

### Installation

```bash
# Make executable (already done if you just created it)
chmod +x pipeline.py

# Or just run with python
python pipeline.py --help
```

### Usage

```bash
# Show help
python pipeline.py --help

# Common operations
python pipeline.py fetch                    # Fetch bills
python pipeline.py filter                   # Run filter pass
python pipeline.py analyze                  # Run analysis pass
python pipeline.py run                      # Full pipeline

# Test mode
python pipeline.py run --test               # Quick test (5 bills)
python pipeline.py filter --test            # Test filter
python pipeline.py analyze --test           # Test analysis

# With options
python pipeline.py fetch --state NY --year 2024
python pipeline.py filter --test --test-count 10
python pipeline.py run --state CA --test

# View results
python pipeline.py results                  # Show summary
python pipeline.py view                     # Show detailed results

# Docker management
python pipeline.py shell                    # Open shell
python pipeline.py logs                     # View logs
python pipeline.py status                   # Container status

# Utilities
python pipeline.py check                    # Check configuration
python pipeline.py clean                    # Clean data
python pipeline.py clean --yes              # Skip confirmation
```

### Examples

```bash
# Run test for different state
python pipeline.py fetch --state NY
python pipeline.py filter --test
python pipeline.py analyze --test
python pipeline.py results

# Full production run with custom state
python pipeline.py run --state CA --year 2024

# Direct analysis
python pipeline.py analyze --direct --filter-file ../data/filtered/filter_results_alan_ct_bills_2025.json

# Check everything before running
python pipeline.py check
python pipeline.py run
```

---

## Comparison

### Feature Matrix

| Feature | Makefile | run.sh | pipeline.py |
|---------|----------|--------|-------------|
| **Quick commands** | ✅ `make run` | ✅ `./run.sh run` | ✅ `python pipeline.py run` |
| **Help menu** | ✅ `make help` | ✅ `./run.sh help` | ✅ `--help` flag |
| **Tab completion** | ✅ Yes (make) | ❌ No | ❌ No |
| **Test mode** | ✅ `make test` | ✅ `./run.sh test` | ✅ `--test` flag |
| **State selection** | ❌ No | ❌ No | ✅ `--state NY` |
| **Multi-state** | ✅ `make run-multi` | ✅ `./run.sh run-multi` | ❌ No |
| **LegiUI support** | ✅ `make ui` | ✅ `./run.sh ui` | ❌ No |
| **Color output** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Windows compatible** | ❌ No | ❌ No | ✅ Yes |

### Which One Should I Use?

**Use Makefile if:**
- ✅ You're on Mac/Linux
- ✅ You want tab completion
- ✅ You like standardized build tools
- ✅ You want the most features

**Use run.sh if:**
- ✅ You prefer shell scripts
- ✅ You want detailed status messages
- ✅ You want interactive prompts (e.g., for clean)
- ✅ You're comfortable with bash

**Use pipeline.py if:**
- ✅ You're on Windows
- ✅ You prefer Python tools
- ✅ You want command-line arguments (`--state`, `--year`)
- ✅ You want to extend with your own Python code

---

## Common Workflows

### First-Time Setup

```bash
# Method 1: Makefile
make build
make up
make check
make test

# Method 2: run.sh
./run.sh start
./run.sh check
./run.sh test

# Method 3: pipeline.py
python pipeline.py check
python pipeline.py run --test
```

### Regular Production Run

```bash
# Makefile
make run
make results
make ui

# run.sh
./run.sh run
./run.sh results
./run.sh ui

# pipeline.py
python pipeline.py run
python pipeline.py results
```

### Debugging

```bash
# Makefile
make logs          # View logs
make shell         # Open shell
make status        # Check status

# run.sh
./run.sh logs
./run.sh shell
./run.sh status

# pipeline.py
python pipeline.py logs
python pipeline.py shell
python pipeline.py status
```

### Multi-State Processing

```bash
# Makefile
make fetch-multi
make filter-multi
make analyze
make results

# run.sh
./run.sh fetch-multi
./run.sh filter-multi
./run.sh analyze
./run.sh results

# pipeline.py (manual)
python pipeline.py fetch --state CT
python pipeline.py fetch --state NY
python pipeline.py fetch --state CA
python pipeline.py filter
python pipeline.py analyze
```

---

## Advanced Usage

### Custom State and Year

```bash
# Only pipeline.py supports this directly
python pipeline.py fetch --state NY --year 2024
python pipeline.py filter
python pipeline.py analyze

# For Makefile/run.sh, modify fetch script or use exec
make exec CMD="python scripts/fetch_legiscan_bills.py --state NY --year 2024"
./run.sh shell  # then run command manually
```

### Direct Analysis with Pre-filtered Data

```bash
# Makefile
make direct-analyze FILTER_FILE=../data/filtered/filter_results_alan_ct_bills_2025.json

# run.sh
# Edit run.sh or use shell
./run.sh shell
cd scripts
python run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json

# pipeline.py
python pipeline.py analyze --direct --filter-file ../data/filtered/filter_results_alan_ct_bills_2025.json
```

### Running Custom Scripts

```bash
# Makefile
make exec CMD="python scripts/your_script.py"
make run-script SCRIPT="scripts/your_script.py"

# run.sh
./run.sh shell
python scripts/your_script.py

# pipeline.py
# Use shell method
python pipeline.py shell
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Run Pipeline

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build containers
        run: make build

      - name: Run pipeline
        run: make run
        env:
          PORTKEY_API_KEY: ${{ secrets.PORTKEY_API_KEY }}
          LEGISCAN_API_KEY: ${{ secrets.LEGISCAN_API_KEY }}

      - name: View results
        run: make results

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: analysis-results
          path: data/analyzed/
```

### Cron Job Example

```bash
# Add to crontab: crontab -e
# Run weekly on Sunday at midnight
0 0 * * 0 cd /path/to/ai-scraper-ideas && make run && make results | mail -s "Weekly Analysis Results" you@example.com
```

---

## Troubleshooting

### Makefile Issues

```bash
# Error: "make: command not found"
# Install make (usually pre-installed on Mac/Linux)
sudo apt-get install make  # Ubuntu
brew install make         # Mac

# Error: "No rule to make target"
make help  # Check available targets
```

### run.sh Issues

```bash
# Error: "Permission denied"
chmod +x run.sh

# Error: "bash: ./run.sh: No such file or directory"
# Make sure you're in the project root directory
pwd  # Should show /path/to/ai-scraper-ideas
```

### pipeline.py Issues

```bash
# Error: "python: command not found"
python3 pipeline.py --help  # Try python3

# Error: "Permission denied"
chmod +x pipeline.py
# Or just use: python pipeline.py

# Error: "No module named 'subprocess'"
# This should never happen (subprocess is built-in)
# Try: python3 pipeline.py
```

### Docker Issues

```bash
# All methods use Docker, so if Docker isn't running:

# Check Docker status
docker ps

# Start Docker Desktop (Mac)
open -a Docker

# Check containers
make status
# or
./run.sh status
# or
python pipeline.py status
```

---

## Quick Start Cheat Sheet

### Absolute Beginner (Never used this before)

```bash
# 1. Start containers
make up              # or: ./run.sh start   or: docker-compose up -d

# 2. Test with 5 bills
make test            # or: ./run.sh test    or: python pipeline.py run --test

# 3. View results
make results         # or: ./run.sh results or: python pipeline.py results

# 4. Start UI
make ui              # or: ./run.sh ui      or: cd legiUI && npm start
```

### Regular User (Run weekly)

```bash
# Full pipeline
make run             # or: ./run.sh run     or: python pipeline.py run

# View results
make results         # or: ./run.sh results or: python pipeline.py results
```

### Power User (Process all states)

```bash
# Multi-state pipeline
make run-multi       # or: ./run.sh run-multi

# View combined results
make results
```

---

## Summary

**TL;DR:**
- **Just want it to work?** Use `make run`
- **Like shell scripts?** Use `./run.sh run`
- **Prefer Python?** Use `python pipeline.py run`
- **All three do the same thing!** Pick your favorite.

**Most Common Commands:**
```bash
make run             # Full pipeline
make test            # Quick test
make results         # View results
make ui              # Start dashboard
make logs            # Debug
make shell           # Interactive mode
```

---

**Document Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team
