# Quick Commands Reference

The **shortest** way to run the pipeline in Docker.

## The `./dc` Script (Recommended) ⭐

```bash
./dc up         # Start containers
./dc fetch      # Fetch bills
./dc filter     # Filter bills  
./dc analyze    # Analyze bills
./dc shell      # Open shell
./dc logs       # View logs
```

**That's it!** Just 12 characters instead of 88.

## Full Example

```bash
# Setup (one time)
cp .env.example .env
nano .env  # Add API keys

# Run pipeline
./dc up
./dc fetch
./dc filter
./dc analyze

# View results
./dc shell
ls -lh data/analyzed/
exit
```

## All Available Shortcuts

| Task | Command | What It Does |
|------|---------|--------------|
| **Fetch bills** | `./dc fetch` | Fetch from LegiScan |
| **Filter** | `./dc filter` | Run filter pass |
| **Analyze** | `./dc analyze` | Run analysis pass |
| **Direct analyze** | `./dc direct <file>` | Analyze pre-filtered data |
| **Shell** | `./dc shell` | Open bash in container |
| **Logs** | `./dc logs` | View container logs |
| **Start** | `./dc up` | Start containers |
| **Stop** | `./dc down` | Stop containers |
| **Status** | `./dc ps` | Check status |
| **Build** | `./dc build` | Build images |

## Comparison

```bash
# The OLD way (88 characters):
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# The NEW way (12 characters):
./dc filter

# 85% less typing!
```

## Other Options

If you prefer, you can also use:

**Makefile:**
```bash
make filter     # Same as ./dc filter
make run        # Run entire pipeline
```

**run.sh:**
```bash
./run.sh filter # Same as ./dc filter
./run.sh run    # Run entire pipeline
```

**Python CLI:**
```bash
python pipeline.py filter
```

## Which One?

- **Use `./dc`** if you want the shortest commands and pure docker-compose
- **Use `make`** if you want tab completion and advanced features
- **Use `./run.sh`** if you prefer shell scripts
- **Use `pipeline.py`** if you're on Windows or prefer Python

**They all do the same thing!** Pick your favorite.

---

**Full documentation:** [docs/DOCKER_SHORTHAND.md](docs/DOCKER_SHORTHAND.md)
