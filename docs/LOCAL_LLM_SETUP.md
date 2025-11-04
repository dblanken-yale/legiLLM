# Local LLM Setup Guide

Complete guide for running the LegiScan Bill Analysis Pipeline with local LLMs using Ollama.

## Quick Start (Mac M1)

### 1. Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 2. Pull a Model

```bash
# Recommended: Llama 3.1 8B (fast, good quality)
ollama pull llama3.1:8b-instruct

# Alternative: Llama 3.1 70B (best quality, requires more RAM)
ollama pull llama3.1:70b-instruct-q4_K_M

# Alternative: Mistral 7B (efficient baseline)
ollama pull mistral:7b-instruct
```

### 3. Start Ollama Server

```bash
# Start server (runs on http://localhost:11434)
ollama serve

# Or run in background
nohup ollama serve > /dev/null 2>&1 &
```

### 4. Configure the Pipeline

```bash
# Use local LLM configuration
cp config_local_llm.json config.json

# Or set environment variables
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
```

### 5. Run the Pipeline

```bash
cd scripts

# Test with 5 bills
TEST_MODE=true TEST_COUNT=5 python run_filter_pass.py ct_bills_2025

# Run full filter pass
python run_filter_pass.py ct_bills_2025

# Run analysis pass
python run_analysis_pass.py
```

---

## Configuration Options

### Option 1: Full Local LLM

Use `config_local_llm.json` - All processing done locally with Ollama.

```json
{
  "llm": {
    "provider": "ollama",
    "model": "llama3.1:8b-instruct",
    "base_url": "http://localhost:11434/v1"
  }
}
```

**Pros:**
- ✅ $0 cost per run
- ✅ Full privacy (no data leaves your machine)
- ✅ No rate limits

**Cons:**
- ❌ 2-3x slower than remote API
- ❌ Slightly lower quality on edge cases
- ❌ Requires local hardware (Mac M1 with 16GB+ RAM recommended)

---

### Option 2: Hybrid Approach (Recommended)

Use `config_hybrid.json` - Local for filter, remote for analysis.

```json
{
  "llm": {
    "provider": "ollama",
    "model": "llama3.1:8b-instruct"
  }
}
```

Then override for analysis pass:

```bash
# Filter with local LLM
python run_filter_pass.py ct_bills_2025

# Analyze with remote API (set env var)
export LLM_PROVIDER=portkey
export LLM_MODEL=gpt-4o-mini
python run_analysis_pass.py
```

**Pros:**
- ✅ 90% cost savings ($2 vs $30)
- ✅ Maintains quality where it matters
- ✅ Good speed/cost balance

**Best for:** Regular processing of state bills

---

### Option 3: Environment Variables

Override configuration at runtime:

```bash
# Use local LLM
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
export LLM_BASE_URL=http://localhost:11434/v1

# Run scripts
python scripts/run_filter_pass.py ct_bills_2025
```

**Best for:** Testing different models, switching between providers

---

## Model Recommendations

### For Mac M1/M2/M3 (16GB-64GB RAM)

| Model | RAM Required | Speed | Quality | Use Case |
|-------|--------------|-------|---------|----------|
| llama3.1:8b-instruct | 8GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General use, fast |
| mistral:7b-instruct | 6GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐½ | Baseline, very fast |
| llama3.1:70b-q4 | 40GB | ⭐⭐ | ⭐⭐⭐⭐⭐ | Best quality (M1 Ultra only) |

### Performance Comparison

**Filter Pass (4,064 bills):**
- Remote API (GPT-4o-mini): ~3-5 hours
- Ollama 8B (Mac M1): ~8-12 hours
- Ollama 70B (Mac M1 Ultra): ~30-40 hours

**Analysis Pass (68 relevant bills):**
- Remote API: ~15 minutes
- Ollama 8B: ~40 minutes
- Ollama 70B: ~2 hours

---

## Docker Setup

### Option A: Ollama on Host, Pipeline in Docker

**Recommended for Mac M1** - Leverage native Metal GPU acceleration.

```bash
# 1. Start Ollama on host machine
ollama serve

# 2. Update docker-compose.yml to use host network
services:
  legiscan-pipeline:
    environment:
      - LLM_BASE_URL=http://host.docker.internal:11434/v1

# 3. Run pipeline
docker-compose up legiscan-pipeline
```

### Option B: Both in Docker Compose

```bash
# 1. Start Ollama container
docker-compose up -d ollama

# 2. Pull model
docker exec -it legiscan-ollama ollama pull llama3.1:8b-instruct

# 3. Run pipeline
docker-compose up legiscan-pipeline
```

See updated `docker-compose.yml` for full configuration.

---

## Troubleshooting

### "Could not connect to Ollama server"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Check for port conflicts
lsof -i :11434
```

### "Model not found"

```bash
# List available models
ollama list

# Pull the model
ollama pull llama3.1:8b-instruct

# Verify it's available
ollama list | grep llama3.1
```

### Pipeline runs but gets errors

```bash
# Test Ollama directly
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b-instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check logs
tail -f ~/.ollama/logs/server.log
```

### Slow performance

**For Mac M1:**
```bash
# Ensure you're using native binary (not Rosetta)
file $(which ollama)
# Should show: arm64

# Monitor GPU usage
sudo powermetrics --samplers gpu_power -i 1000

# Use smaller quantization
ollama pull llama3.1:8b-instruct-q4_K_M  # 4-bit, faster
```

**Reduce batch size in config:**
```json
{
  "filter_pass": {
    "batch_size": 5  // Reduce from 10
  }
}
```

### Out of memory errors

```bash
# Use smaller model
ollama pull mistral:7b-instruct

# Or use quantized version
ollama pull llama3.1:8b-instruct-q4_K_M
```

---

## Quality Validation

### Compare Results

Use the comparison tool to validate local LLM quality:

```bash
# Run both providers on same data
python scripts/test_llm_providers.py ct_bills_2025 \
  --providers ollama,portkey \
  --sample-size 100

# Output shows:
# - Agreement rate
# - False positives/negatives
# - Category assignment differences
```

### Quality Metrics

**Expected agreement with GPT-4o-mini:**
- Llama 3.1 8B: ~85-90% relevance agreement
- Llama 3.1 70B: ~95-98% relevance agreement
- Mistral 7B: ~80-85% relevance agreement

**If agreement is too low:**
1. Adjust temperature (try 0.1-0.2 for more consistent results)
2. Increase max_tokens if responses are cut off
3. Try a larger model (70B)
4. Use hybrid approach (local filter, remote analysis)

---

## Cost Analysis

### Full Local (Ollama 8B)
- **Cost:** $0
- **Time:** ~10 hours for 4,000 bills
- **Hardware:** Mac M1 (16GB+) or equivalent
- **Best for:** High-volume processing, privacy-sensitive data

### Hybrid (Ollama filter + GPT-4o analysis)
- **Cost:** ~$2 per run (vs $30 full remote)
- **Time:** ~6 hours for 4,000 bills
- **Quality:** Same as full remote
- **Best for:** Regular processing, budget-conscious

### Full Remote (Current)
- **Cost:** ~$30 per run
- **Time:** ~4 hours for 4,000 bills
- **Quality:** Best
- **Best for:** One-time processing, maximum quality

---

## Advanced Configuration

### Multiple Models

```json
{
  "filter_pass": {
    "llm": {
      "provider": "ollama",
      "model": "mistral:7b"  // Fast filter
    }
  },
  "analysis_pass": {
    "llm": {
      "provider": "ollama",
      "model": "llama3.1:70b"  // Quality analysis
    }
  }
}
```

*Note: Per-pass LLM configuration not yet implemented. Use environment variables to switch between passes.*

### Custom Ollama Host

```bash
# Run Ollama on different machine
ollama serve --host 0.0.0.0:11434

# Configure pipeline
export LLM_BASE_URL=http://192.168.1.100:11434/v1
```

### GPU Acceleration (Linux)

```yaml
# docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## Next Steps

1. **Try it out:** Start with test mode (5 bills)
2. **Validate quality:** Compare results with remote API
3. **Optimize:** Adjust batch size and timeout for your hardware
4. **Scale up:** Run full pipeline once confident

For more information:
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Model Library](https://ollama.com/library)
- [CLAUDE.md](../CLAUDE.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
