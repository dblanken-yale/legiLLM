# Docker Deployment Guide

Complete guide for running the LegiScan Bill Analysis Pipeline in Docker with all LLM provider options.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Setup Options](#docker-setup-options)
3. [Configuration by LLM Provider](#configuration-by-llm-provider)
4. [Running the Pipeline](#running-the-pipeline)
5. [LegiUI in Docker](#legiui-in-docker)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## Quick Start

### Prerequisites

```bash
# Verify Docker is installed
docker --version
# Expected: Docker version 20.x or higher

docker-compose --version
# Expected: Docker Compose version 2.x or higher
```

### Minimal Setup (Portkey)

```bash
# 1. Clone repository
cd /path/to/ai-scraper-ideas

# 2. Create .env file
cat > .env << 'EOF'
PORTKEY_API_KEY=your_portkey_api_key_here
LEGISCAN_API_KEY=your_legiscan_api_key_here
TEST_MODE=false
TEST_COUNT=5
EOF

# 3. Build and start container
docker-compose up -d

# 4. Verify container is running
docker-compose ps

# 5. Run fetch script
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# 6. Run filter pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# 7. Run analysis pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
```

---

## Docker Setup Options

### Option 1: Docker Compose (Recommended)

Best for local development and testing.

**Advantages:**
- ✅ Simplified configuration
- ✅ Easy volume management
- ✅ Environment variable management
- ✅ Multi-container orchestration

**Use Cases:**
- Local development
- Testing different configurations
- Running multiple services (pipeline + UI)

### Option 2: Standalone Docker

Best for single-container deployments or production.

**Advantages:**
- ✅ Simpler deployment
- ✅ More control over runtime
- ✅ Better for CI/CD pipelines

**Use Cases:**
- Production deployments
- Azure Container Instances
- Kubernetes pods

### Option 3: Docker with Ollama (Local LLM)

Best for cost-effective, privacy-focused deployments.

**Advantages:**
- ✅ No API costs
- ✅ Full data privacy
- ✅ No rate limits

**Use Cases:**
- High-volume processing
- Sensitive data
- Budget-constrained projects

---

## Configuration by LLM Provider

### Scenario 1: Docker + Portkey (OpenAI via Proxy)

**When to use:** Simple setup, cloud-based processing, minimal configuration.

#### Step 1: Create Environment File

```bash
cat > .env << 'EOF'
# Portkey Configuration
PORTKEY_API_KEY=pk_live_xxxxxxxxxxxxxxxx
LEGISCAN_API_KEY=xxxxxxxxxxxxxxxx

# Optional: Test Mode
TEST_MODE=false
TEST_COUNT=5

# Storage
STORAGE_BACKEND=local
EOF
```

#### Step 2: Create/Verify docker-compose.yml

The existing `docker-compose.yml` is already configured for this. Verify it contains:

```yaml
version: '3.8'

services:
  legiscan-pipeline:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: legiscan-pipeline
    environment:
      - PORTKEY_API_KEY=${PORTKEY_API_KEY}
      - LEGISCAN_API_KEY=${LEGISCAN_API_KEY}
      - TEST_MODE=${TEST_MODE:-false}
      - TEST_COUNT=${TEST_COUNT:-5}
      - STORAGE_BACKEND=local
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
      - ./src:/app/src
      - ./scripts:/app/scripts
      - ./prompts:/app/prompts
      - ./config.json:/app/config.json
    working_dir: /app
    stdin_open: true
    tty: true
    command: tail -f /dev/null
    networks:
      - legiscan-network

networks:
  legiscan-network:
    driver: bridge
```

#### Step 3: Build and Start

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# Verify it's running
docker-compose ps
# Expected output: legiscan-pipeline running
```

#### Step 4: Run Pipeline

```bash
# Fetch bills from LegiScan
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# Run filter pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Run analysis pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# Or run direct analysis with pre-filtered data
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_direct_analysis.py ../data/filtered/filter_results_ct_bills_2025.json"
```

#### Step 5: Access Results

```bash
# View results (from host machine)
ls -lh data/analyzed/

# Copy results out of container (if needed)
docker cp legiscan-pipeline:/app/data/analyzed/analysis_results_relevant.json ./
```

---

### Scenario 2: Docker + Azure OpenAI

**When to use:** Enterprise deployments, compliance requirements, Azure ecosystem integration.

#### Step 1: Create Environment File

```bash
cat > .env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# LegiScan Configuration
LEGISCAN_API_KEY=your_legiscan_key_here

# Optional: Test Mode
TEST_MODE=false
TEST_COUNT=5

# Storage
STORAGE_BACKEND=local
EOF
```

#### Step 2: Create Azure Configuration File

```bash
cat > config.json << 'EOF'
{
  "llm": {
    "provider": "azure",
    "deployment_name": "gpt-4o-mini",
    "endpoint": null,
    "api_key": null,
    "api_version": "2024-02-15-preview"
  },
  "model": "gpt-4o-mini",
  "temperature": 0.3,
  "max_tokens": 2000,
  "filter_pass": {
    "batch_size": 50,
    "timeout": 180
  },
  "analysis_pass": {
    "timeout": 90,
    "api_delay": 1.0
  },
  "legiscan": {
    "cache_enabled": true,
    "cache_directory": "data/cache/legiscan_cache"
  }
}
EOF
```

**Note:** Setting `endpoint: null` and `api_key: null` tells the app to use environment variables.

#### Step 3: Build and Start

```bash
# Build with Azure configuration
docker-compose build

# Start container
docker-compose up -d

# Verify Azure OpenAI connectivity
docker-compose exec legiscan-pipeline python -c "
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version='2024-02-15-preview',
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

response = client.chat.completions.create(
    model=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=10
)

print('✅ Azure OpenAI connection successful!')
print(f'Response: {response.choices[0].message.content}')
"
```

#### Step 4: Run Pipeline

```bash
# Fetch bills
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# Filter pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Analysis pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
```

---

### Scenario 3: Docker + Ollama (Local LLM)

**When to use:** Cost optimization, data privacy, no external API dependencies.

#### Option A: Ollama on Host, Pipeline in Docker (Recommended for Mac M1)

**Why:** Leverages native Metal GPU acceleration on macOS.

##### Step 1: Install and Start Ollama on Host

```bash
# Install Ollama on your Mac
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.1:8b-instruct

# Start Ollama server
ollama serve
# Leave this terminal running
```

##### Step 2: Configure Docker to Use Host Ollama

```bash
# Create environment file
cat > .env << 'EOF'
# Ollama Configuration (connecting to host)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b-instruct
LLM_BASE_URL=http://host.docker.internal:11434/v1

# LegiScan Configuration
LEGISCAN_API_KEY=your_legiscan_key_here

# Test Mode
TEST_MODE=false
TEST_COUNT=5

# Storage
STORAGE_BACKEND=local
EOF
```

##### Step 3: Update docker-compose.yml

```bash
# Create a docker-compose override file
cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  legiscan-pipeline:
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - LLM_BASE_URL=${LLM_BASE_URL:-http://host.docker.internal:11434/v1}
EOF
```

##### Step 4: Build and Test

```bash
# Build and start
docker-compose up -d

# Test Ollama connectivity from container
docker-compose exec legiscan-pipeline curl http://host.docker.internal:11434/api/tags
# Should return JSON with available models

# Test with Python
docker-compose exec legiscan-pipeline python -c "
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv('LLM_BASE_URL', 'http://host.docker.internal:11434/v1'),
    api_key='ollama'  # Ollama doesn't need real API key
)

response = client.chat.completions.create(
    model=os.getenv('LLM_MODEL', 'llama3.1:8b-instruct'),
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=10
)

print('✅ Ollama connection successful!')
print(f'Response: {response.choices[0].message.content}')
"
```

##### Step 5: Run Pipeline

```bash
# Fetch bills
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# Filter pass (with local LLM)
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Analysis pass
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
```

---

#### Option B: Both Pipeline and Ollama in Docker

**Why:** Fully containerized, portable across environments.

##### Step 1: Create Extended docker-compose.yml

```bash
cat > docker-compose.ollama.yml << 'EOF'
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: legiscan-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - legiscan-network
    # Uncomment for GPU support on Linux
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  legiscan-pipeline:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: legiscan-pipeline
    depends_on:
      - ollama
    environment:
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama3.1:8b-instruct
      - LLM_BASE_URL=http://ollama:11434/v1
      - LEGISCAN_API_KEY=${LEGISCAN_API_KEY}
      - TEST_MODE=${TEST_MODE:-false}
      - TEST_COUNT=${TEST_COUNT:-5}
      - STORAGE_BACKEND=local
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
      - ./src:/app/src
      - ./scripts:/app/scripts
      - ./prompts:/app/prompts
      - ./config.json:/app/config.json
    working_dir: /app
    stdin_open: true
    tty: true
    command: tail -f /dev/null
    networks:
      - legiscan-network

networks:
  legiscan-network:
    driver: bridge

volumes:
  ollama-data:
EOF
```

##### Step 2: Start Services

```bash
# Start Ollama first
docker-compose -f docker-compose.ollama.yml up -d ollama

# Wait for Ollama to be ready (about 10 seconds)
sleep 10

# Pull the model
docker exec -it legiscan-ollama ollama pull llama3.1:8b-instruct

# Verify model is available
docker exec -it legiscan-ollama ollama list

# Start the pipeline container
docker-compose -f docker-compose.ollama.yml up -d legiscan-pipeline

# Verify both are running
docker-compose -f docker-compose.ollama.yml ps
```

##### Step 3: Test Connectivity

```bash
# Test Ollama from pipeline container
docker-compose -f docker-compose.ollama.yml exec legiscan-pipeline curl http://ollama:11434/api/tags

# Test with Python
docker-compose -f docker-compose.ollama.yml exec legiscan-pipeline python -c "
from openai import OpenAI

client = OpenAI(
    base_url='http://ollama:11434/v1',
    api_key='ollama'
)

response = client.chat.completions.create(
    model='llama3.1:8b-instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=10
)

print('✅ Ollama connection successful!')
print(f'Response: {response.choices[0].message.content}')
"
```

##### Step 4: Run Pipeline

```bash
# Fetch bills
docker-compose -f docker-compose.ollama.yml exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# Filter pass
docker-compose -f docker-compose.ollama.yml exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Analysis pass
docker-compose -f docker-compose.ollama.yml exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
```

---

## Running the Pipeline

### Common Operations

#### Interactive Shell Access

```bash
# Enter container bash shell
docker-compose exec legiscan-pipeline bash

# Now you can run commands directly
cd scripts
python fetch_legiscan_bills.py
python run_filter_pass.py
python run_analysis_pass.py
exit
```

#### Test Mode (Process 5 Bills Only)

```bash
# Set test mode in .env
echo "TEST_MODE=true" >> .env
echo "TEST_COUNT=5" >> .env

# Restart container to pick up changes
docker-compose restart

# Run pipeline
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
```

#### Check Logs

```bash
# View container logs
docker-compose logs -f legiscan-pipeline

# View specific script output
docker-compose exec legiscan-pipeline tail -f data/logs/pipeline.log
```

#### Monitor Resource Usage

```bash
# View container stats
docker stats legiscan-pipeline

# View detailed container info
docker inspect legiscan-pipeline
```

### Pipeline Workflow

#### Full Workflow (Connecticut 2025 Bills)

```bash
# Step 1: Start containers
docker-compose up -d

# Step 2: Fetch bills from LegiScan
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py
# Output: data/raw/ct_bills_2025.json

# Step 3: Run filter pass (batch processing)
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
# Output: data/filtered/filter_results_ct_bills_2025.json

# Step 4: Run analysis pass (full text analysis)
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
# Output:
#   data/analyzed/analysis_results_relevant.json
#   data/analyzed/analysis_results_not_relevant.json

# Step 5: View results
docker-compose exec legiscan-pipeline ls -lh data/analyzed/
```

#### Alternative: Direct Analysis with Pre-filtered Data

```bash
# If you have pre-filtered data from vector similarity, etc.
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json"
# Output: data/analyzed/analysis_alan_ct_bills_2025_relevant.json
```

#### Multiple States

```bash
# Fetch from multiple states
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py --state CT
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py --state NY
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py --state CA

# Process each state
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py ct_bills_2025"
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py ny_bills_2025"
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py ca_bills_2025"
```

---

## LegiUI in Docker

### Option 1: Separate Development Server

Run LegiUI outside Docker for development:

```bash
# On host machine
cd legiUI
npm install
npm run load-data  # Load data from ../data/analyzed/
npm run dev        # Starts on http://localhost:5173
```

### Option 2: Add LegiUI to docker-compose

```bash
cat >> docker-compose.yml << 'EOF'

  legiui:
    build:
      context: ./legiUI
      dockerfile: Dockerfile.ui
    container_name: legiui
    ports:
      - "5173:5173"
    volumes:
      - ./legiUI:/app
      - /app/node_modules
      - ./data:/app/data
    environment:
      - NODE_ENV=development
    depends_on:
      - legiscan-pipeline
    networks:
      - legiscan-network
    command: npm run dev -- --host
EOF
```

Create LegiUI Dockerfile:

```bash
cat > legiUI/Dockerfile.ui << 'EOF'
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application files
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Default command
CMD ["npm", "run", "dev", "--", "--host"]
EOF
```

Start LegiUI:

```bash
# Build and start
docker-compose up -d legiui

# Access UI
open http://localhost:5173
```

### Option 3: Production Build

```bash
# Build production assets
docker-compose exec legiui npm run build

# Serve with nginx
cat > legiUI/Dockerfile.nginx << 'EOF'
FROM node:20-slim AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build and run
docker build -f legiUI/Dockerfile.nginx -t legiui:prod ./legiUI
docker run -d -p 8080:80 legiui:prod

# Access at http://localhost:8080
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs legiscan-pipeline

# Common issue: Port already in use
docker-compose down
docker ps -a  # Check for zombie containers
docker rm -f legiscan-pipeline  # Force remove

# Rebuild from scratch
docker-compose down -v  # Remove volumes too
docker-compose build --no-cache
docker-compose up -d
```

### Cannot Connect to Ollama (Option A)

```bash
# Verify Ollama is running on host
curl http://localhost:11434/api/tags

# Test from inside container
docker-compose exec legiscan-pipeline curl http://host.docker.internal:11434/api/tags

# On Linux, use host IP instead of host.docker.internal
ip addr show docker0
# Use the IP shown (usually 172.17.0.1)
# Update LLM_BASE_URL in .env to http://172.17.0.1:11434/v1
```

### Cannot Connect to Ollama (Option B)

```bash
# Check Ollama container is running
docker ps | grep ollama

# Check Ollama logs
docker logs legiscan-ollama

# Test connectivity
docker exec -it legiscan-ollama ollama list

# Restart Ollama
docker-compose -f docker-compose.ollama.yml restart ollama
```

### API Key Errors

```bash
# Verify environment variables are loaded
docker-compose exec legiscan-pipeline env | grep API_KEY

# If empty, check .env file exists
cat .env

# Restart to reload environment
docker-compose restart
```

### Data Not Persisting

```bash
# Check volume mounts
docker inspect legiscan-pipeline | grep -A 10 Mounts

# Verify data directory exists on host
ls -la data/

# Fix permissions if needed
sudo chown -R $USER:$USER data/
```

### Slow Performance

```bash
# Check resource usage
docker stats legiscan-pipeline

# Increase Docker resources (Docker Desktop settings):
# - CPUs: 4+
# - Memory: 8GB+
# - Swap: 2GB+

# For Ollama, reduce batch size in config.json
docker-compose exec legiscan-pipeline bash -c 'cat > config.json << EOF
{
  "filter_pass": {
    "batch_size": 5
  }
}
EOF'
```

### Volume Permission Errors

```bash
# Create directories with correct permissions
mkdir -p data/{raw,filtered,analyzed,cache/legiscan_cache}
chmod -R 777 data/

# Or run container as current user
docker-compose exec -u $(id -u):$(id -g) legiscan-pipeline bash
```

---

## Production Deployment

### Best Practices

#### 1. Use Multi-Stage Builds

Already implemented in Dockerfile:

```dockerfile
FROM python:3.11-slim AS builder
# Build stage...

FROM python:3.11-slim
# Runtime stage (smaller image)
```

#### 2. Don't Mount Source Code

Remove source code volumes in production:

```bash
# Create docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  legiscan-pipeline:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: legiscan-pipeline
    environment:
      - PORTKEY_API_KEY=${PORTKEY_API_KEY}
      - LEGISCAN_API_KEY=${LEGISCAN_API_KEY}
      - STORAGE_BACKEND=local
    volumes:
      - ./data:/app/data  # Only mount data
    restart: unless-stopped
    networks:
      - legiscan-network

networks:
  legiscan-network:
    driver: bridge
EOF

# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Use Secrets Management

```bash
# Use Docker secrets instead of .env file
echo "pk_live_xxxxx" | docker secret create portkey_api_key -
echo "xxxxx" | docker secret create legiscan_api_key -

# Update docker-compose to use secrets
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  legiscan-pipeline:
    # ... other config ...
    secrets:
      - portkey_api_key
      - legiscan_api_key
    environment:
      - PORTKEY_API_KEY_FILE=/run/secrets/portkey_api_key
      - LEGISCAN_API_KEY_FILE=/run/secrets/legiscan_api_key

secrets:
  portkey_api_key:
    external: true
  legiscan_api_key:
    external: true
EOF
```

#### 4. Health Checks

Already configured in Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from src.storage_provider import StorageProviderFactory; sys.exit(0)"
```

#### 5. Logging

```bash
# Configure logging driver
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  legiscan-pipeline:
    # ... other config ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

#### 6. Resource Limits

```bash
# Add resource constraints
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  legiscan-pipeline:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
EOF
```

### Azure Container Instances

See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for detailed Azure deployment instructions.

Quick deployment:

```bash
# Build and push to Azure Container Registry
az acr build --registry myregistry --image legiscan-pipeline:latest .

# Deploy to Container Instance
az container create \
  --resource-group rg-legiscan \
  --name legiscan-pipeline \
  --image myregistry.azurecr.io/legiscan-pipeline:latest \
  --cpu 4 --memory 8 \
  --environment-variables \
    PORTKEY_API_KEY=$PORTKEY_API_KEY \
    LEGISCAN_API_KEY=$LEGISCAN_API_KEY \
  --azure-file-volume-account-name mystorageacct \
  --azure-file-volume-account-key $STORAGE_KEY \
  --azure-file-volume-share-name legiscan-data \
  --azure-file-volume-mount-path /app/data
```

### Kubernetes

```yaml
# legiscan-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legiscan-pipeline
spec:
  replicas: 1
  selector:
    matchLabels:
      app: legiscan-pipeline
  template:
    metadata:
      labels:
        app: legiscan-pipeline
    spec:
      containers:
      - name: legiscan-pipeline
        image: your-registry/legiscan-pipeline:latest
        env:
        - name: PORTKEY_API_KEY
          valueFrom:
            secretKeyRef:
              name: legiscan-secrets
              key: portkey-api-key
        - name: LEGISCAN_API_KEY
          valueFrom:
            secretKeyRef:
              name: legiscan-secrets
              key: legiscan-api-key
        volumeMounts:
        - name: data
          mountPath: /app/data
        resources:
          limits:
            memory: "8Gi"
            cpu: "4"
          requests:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: legiscan-data-pvc
```

Deploy:

```bash
# Create secrets
kubectl create secret generic legiscan-secrets \
  --from-literal=portkey-api-key=$PORTKEY_API_KEY \
  --from-literal=legiscan-api-key=$LEGISCAN_API_KEY

# Deploy
kubectl apply -f legiscan-deployment.yaml

# Check status
kubectl get pods
kubectl logs -f <pod-name>
```

---

## Summary

### Quick Reference

| Scenario | Command |
|----------|---------|
| **Build** | `docker-compose build` |
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose down` |
| **Logs** | `docker-compose logs -f` |
| **Shell** | `docker-compose exec legiscan-pipeline bash` |
| **Fetch Bills** | `docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py` |
| **Filter** | `docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"` |
| **Analyze** | `docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"` |
| **Test Mode** | `TEST_MODE=true TEST_COUNT=5 docker-compose up -d` |

### File Locations in Container

| Path | Description |
|------|-------------|
| `/app/data/raw/` | Raw LegiScan bill data |
| `/app/data/filtered/` | Filter pass results |
| `/app/data/analyzed/` | Analysis pass results |
| `/app/data/cache/` | LegiScan API cache |
| `/app/scripts/` | Python scripts |
| `/app/src/` | Source code |
| `/app/prompts/` | AI prompts |
| `/app/config.json` | Configuration |

### Next Steps

- For Azure deployment: See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- For local LLM setup: See [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)
- For production best practices: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- For common scenarios: See [QUICK_START_SCENARIOS.md](QUICK_START_SCENARIOS.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team
