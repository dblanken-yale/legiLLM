# Convenience Tools - Quick Reference

Three ways to run the LegiScan pipeline in Docker. Pick your favorite!

## 🎯 Quick Commands

### Run Full Pipeline
```bash
make run              # Makefile
./run.sh run          # Shell script  
python pipeline.py run   # Python CLI
```

### Test with 5 Bills
```bash
make test
./run.sh test
python pipeline.py run --test
```

### View Results
```bash
make results
./run.sh results
python pipeline.py results
```

### Start Dashboard
```bash
make ui
./run.sh ui
cd legiUI && npm start
```

---

## 📋 All Available Commands

| Task | Makefile | Shell Script | Python CLI |
|------|----------|--------------|------------|
| **Fetch bills** | `make fetch` | `./run.sh fetch` | `python pipeline.py fetch` |
| **Filter pass** | `make filter` | `./run.sh filter` | `python pipeline.py filter` |
| **Analysis pass** | `make analyze` | `./run.sh analyze` | `python pipeline.py analyze` |
| **Full pipeline** | `make run` | `./run.sh run` | `python pipeline.py run` |
| **Test mode** | `make test` | `./run.sh test` | `python pipeline.py run --test` |
| **View results** | `make results` | `./run.sh results` | `python pipeline.py results` |
| **Open shell** | `make shell` | `./run.sh shell` | `python pipeline.py shell` |
| **View logs** | `make logs` | `./run.sh logs` | `python pipeline.py logs` |
| **Start UI** | `make ui` | `./run.sh ui` | N/A |

---

## 🚀 Getting Started

### First Time
```bash
# 1. Setup
cp .env.example .env
# Edit .env with your API keys

# 2. Quick test (recommended)
make test              # Test with 5 bills

# 3. View results
make results

# 4. Run full pipeline
make run
```

### Regular Use
```bash
make run               # Run pipeline
make results           # Check results
make ui                # View in dashboard
```

---

## 📚 Full Documentation

- **[Convenience Commands Guide](docs/CONVENIENCE_COMMANDS.md)** - Complete reference
- **[Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)** - Docker details
- **[Quick Start Scenarios](docs/QUICK_START_SCENARIOS.md)** - Step-by-step recipes

---

## 🎨 Which Tool Should I Use?

**Makefile** (recommended)
- ✅ Tab completion
- ✅ Most features
- ✅ Standard build tool
- ❌ Mac/Linux only

**run.sh**
- ✅ Detailed messages
- ✅ Interactive prompts
- ✅ Easy to customize
- ❌ Mac/Linux only

**pipeline.py**
- ✅ Works on Windows
- ✅ Command-line arguments
- ✅ Easy to extend
- ✅ Python programmers

---

## 💡 Pro Tips

```bash
# See all available commands
make help

# Check configuration before running
make check            # or ./run.sh check

# Watch logs in real-time
make logs             # or ./run.sh logs

# Process multiple states
make fetch-multi
make filter-multi
make analyze

# Clean up when done
make clean-data       # Remove all data
make clean-cache      # Clear API cache
```

---

**For complete documentation, see [docs/CONVENIENCE_COMMANDS.md](docs/CONVENIENCE_COMMANDS.md)**
