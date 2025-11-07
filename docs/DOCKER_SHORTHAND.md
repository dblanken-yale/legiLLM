# Docker Compose Shorthand Commands

Super simple way to run the pipeline using Docker Compose directly.

## Quick Start

```bash
# Start containers
./dc up

# Run commands
./dc fetch          # Fetch bills
./dc filter         # Filter bills
./dc analyze        # Analyze bills

# That's it!
```

## The `./dc` Wrapper

Instead of typing `docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"`, you can now just type:

```bash
./dc filter
```

### All Commands

```bash
./dc fetch              # Fetch bills from LegiScan
./dc filter             # Run filter pass
./dc analyze            # Run analysis pass
./dc direct <file>      # Run direct analysis on pre-filtered data

./dc shell              # Open bash shell
./dc logs               # View logs
./dc up                 # Start containers
./dc down               # Stop containers
./dc ps                 # Container status
./dc build              # Build images
```

### Examples

```bash
# Full workflow
./dc up                 # Start
./dc fetch              # Get bills
./dc filter             # Filter them
./dc analyze            # Analyze them

# Direct analysis with pre-filtered data
./dc direct ../data/filtered/filter_results_alan_ct_bills_2025.json

# Debug
./dc logs               # Check logs
./dc shell              # Open shell
```

## How It Works

The `./dc` script is a tiny wrapper around `docker-compose run`. It:

1. Maps simple commands to docker-compose services
2. Handles file arguments
3. Uses `docker-compose run --rm` so containers auto-cleanup
4. Runs commands directly (no persistent container needed for one-off tasks)

### Under the Hood

```bash
# When you type:
./dc filter

# It runs:
docker-compose run --rm filter

# Which is defined in docker-compose.yml as:
services:
  filter:
    extends: legiscan-pipeline
    command: bash -c "cd scripts && python run_filter_pass.py"
```

## Comparison with Other Methods

| Method | Command | Length |
|--------|---------|--------|
| **Long Form** | `docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"` | 88 chars |
| **Makefile** | `make filter` | 11 chars |
| **dc wrapper** | `./dc filter` | 12 chars |

All three do the same thing, but `./dc` is:
- ✅ Native docker-compose (no make, no bash scripts)
- ✅ Super short
- ✅ Easy to understand
- ✅ Easy to customize

## Customizing

Edit the `./dc` script to add your own commands:

```bash
#!/bin/bash
SERVICE=$1
shift

case "$SERVICE" in
    my-custom-task)
        docker-compose run --rm legiscan-pipeline python scripts/my_script.py "$@"
        ;;
    # ... other commands
esac
```

Then use:
```bash
./dc my-custom-task
```

## Using Docker Compose Directly (Without ./dc)

If you prefer not to use the wrapper, you can use docker-compose directly:

```bash
# Start main container
docker-compose up -d

# Run one-off commands
docker-compose run --rm fetch
docker-compose run --rm filter
docker-compose run --rm analyze

# Or use the persistent container
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
```

### Why `docker-compose run` vs `exec`?

**`docker-compose run --rm <service>`**
- ✅ Creates a new container
- ✅ Runs the command
- ✅ Deletes container when done (`--rm`)
- ✅ Perfect for one-off tasks
- ❌ Slightly slower startup

**`docker-compose exec <service> <command>`**
- ✅ Runs in existing container
- ✅ Faster (no startup)
- ❌ Requires container to be already running
- ❌ Requires typing full command

## Full Workflow Example

```bash
# Setup (one time)
cp .env.example .env
# Edit .env with your API keys

# Build
./dc build

# Start
./dc up

# Run pipeline
./dc fetch          # ~30 seconds
./dc filter         # ~3-5 hours
./dc analyze        # ~15 minutes

# Check results
./dc shell
ls -lh data/analyzed/
exit

# Stop
./dc down
```

## Test Mode

```bash
# Set test mode in .env
echo "TEST_MODE=true" >> .env
echo "TEST_COUNT=5" >> .env

# Restart to pick up env changes
./dc down
./dc up

# Run test (processes 5 bills)
./dc filter
./dc analyze
```

## Multi-State Processing

```bash
# Fetch multiple states
./dc fetch  # Default: CT
# For other states, use shell:
./dc shell
python scripts/fetch_legiscan_bills.py --state NY
python scripts/fetch_legiscan_bills.py --state CA
exit

# Filter all states
./dc shell
cd scripts
for file in ../data/raw/*_bills_*.json; do
    basename=$(basename "$file" .json)
    python run_filter_pass.py "$basename"
done
exit

# Analyze all
./dc analyze
```

## Advanced: Adding More Services

You can extend `docker-compose.yml` to add more shorthand commands:

```yaml
services:
  # ... existing services ...

  test:
    extends: legiscan-pipeline
    profiles: ["cli"]
    environment:
      - TEST_MODE=true
      - TEST_COUNT=5
    command: bash -c "cd scripts && python run_filter_pass.py && python run_analysis_pass.py"

  results:
    extends: legiscan-pipeline
    profiles: ["cli"]
    command: python -c "import json; bills = json.load(open('data/analyzed/analysis_results_relevant.json')); print(f'{len(bills)} relevant bills')"
```

Then use:
```bash
docker-compose run --rm test       # Quick test
docker-compose run --rm results    # Show results
```

Or add to `./dc`:
```bash
case "$SERVICE" in
    test)
        TEST_MODE=true TEST_COUNT=5 docker-compose run --rm test
        ;;
    results)
        docker-compose run --rm results
        ;;
esac
```

Then:
```bash
./dc test
./dc results
```

## Comparison: Three Approaches

### 1. Pure Docker Compose (Verbose)
```bash
docker-compose up -d
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
```

### 2. Using ./dc (Recommended for Docker Purists)
```bash
./dc up
./dc fetch
./dc filter
./dc analyze
```

### 3. Using Makefile (Recommended for Power Users)
```bash
make up
make fetch
make filter
make analyze
# or just: make run
```

## When to Use Each

**Use `./dc` if:**
- ✅ You want to stay close to docker-compose
- ✅ You prefer simple shell scripts
- ✅ You want easy customization
- ✅ You don't want to learn make

**Use `Makefile` if:**
- ✅ You want tab completion
- ✅ You want more advanced features
- ✅ You're comfortable with make
- ✅ You want the most comprehensive tooling

**Use direct docker-compose if:**
- ✅ You want complete control
- ✅ You want to see exactly what's running
- ✅ You're learning Docker
- ✅ You want no abstractions

## Pro Tips

### 1. Create an alias
```bash
# Add to ~/.bashrc or ~/.zshrc
alias dc='./dc'

# Then use:
dc fetch
dc filter
dc analyze
```

### 2. Tab completion for ./dc
```bash
# Add to ~/.bashrc or ~/.zshrc
_dc_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=( $(compgen -W "fetch filter analyze direct shell logs up down ps build" -- $cur) )
}
complete -F _dc_completion dc
```

### 3. Chain commands
```bash
./dc fetch && ./dc filter && ./dc analyze
```

### 4. Background execution
```bash
./dc up
./dc filter &
# Do other work
wait
./dc analyze
```

## Summary

**Shortest possible commands:**
```bash
./dc fetch      # Instead of 68 characters
./dc filter     # Instead of 88 characters
./dc analyze    # Instead of 89 characters
```

**That's 85%+ less typing!**

---

**Document Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team
