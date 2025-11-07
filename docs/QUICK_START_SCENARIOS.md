# Quick Start Scenarios

Cookbook-style guides for common deployment scenarios. Each scenario includes complete, copy-paste ready commands from zero to running pipeline.

## Table of Contents

1. [Scenario 1: First-Time User (Local + Portkey)](#scenario-1-first-time-user-local--portkey)
2. [Scenario 2: Docker + Azure OpenAI + Local Files](#scenario-2-docker--azure-openai--local-files)
3. [Scenario 3: Docker + Ollama (Zero Cost)](#scenario-3-docker--ollama-zero-cost)
4. [Scenario 4: Hybrid Approach (Best Value)](#scenario-4-hybrid-approach-best-value)
5. [Scenario 5: Production Azure Deployment](#scenario-5-production-azure-deployment)
6. [Scenario 6: Multiple States Processing](#scenario-6-multiple-states-processing)
7. [Scenario 7: LegiUI Dashboard Setup](#scenario-7-legiui-dashboard-setup)
8. [Scenario 8: Testing with 5 Bills](#scenario-8-testing-with-5-bills)

---

## Scenario 1: First-Time User (Local + Portkey)

**Goal:** Get up and running in 10 minutes with minimal setup.

**What You'll Get:**
- Running pipeline on your local machine
- Cloud-based AI processing (Portkey)
- Results saved locally
- Easiest debugging and iteration

**Prerequisites:**
- Python 3.11+
- Portkey API key ([get one here](https://portkey.ai))
- LegiScan API key ([get one here](https://legiscan.com/legiscan))

### Step-by-Step

```bash
# ========================================
# STEP 1: Clone Repository
# ========================================
cd ~  # or wherever you keep projects
git clone https://github.com/your-org/ai-scraper-ideas.git
cd ai-scraper-ideas

# Verify you're in the right place
ls
# Expected: README.md, scripts/, src/, requirements.txt, etc.

# ========================================
# STEP 2: Create Virtual Environment
# ========================================
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Verify activation (should show venv in prompt)
which python
# Expected: /path/to/ai-scraper-ideas/venv/bin/python

# ========================================
# STEP 3: Install Dependencies
# ========================================
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import openai; print('✅ Dependencies installed')"

# ========================================
# STEP 4: Configure Environment Variables
# ========================================
cp .env.example .env

# Edit .env file with your API keys
cat > .env << 'EOF'
# Portkey Configuration
PORTKEY_API_KEY=pk_live_YOUR_KEY_HERE
LEGISCAN_API_KEY=YOUR_LEGISCAN_KEY_HERE

# Test Mode (optional)
TEST_MODE=false
TEST_COUNT=5
EOF

# Replace YOUR_KEY_HERE with actual keys:
nano .env  # or vim, emacs, code, etc.

# ========================================
# STEP 5: Verify Configuration
# ========================================
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
assert os.getenv('PORTKEY_API_KEY'), 'PORTKEY_API_KEY not set'
assert os.getenv('LEGISCAN_API_KEY'), 'LEGISCAN_API_KEY not set'
print('✅ Configuration verified')
"

# ========================================
# STEP 6: Fetch Bills from LegiScan
# ========================================
cd scripts

python fetch_legiscan_bills.py
# Expected output:
# Fetching bills for state: CT, year: 2025
# Fetched 4,064 bills
# Saved to: ../data/raw/ct_bills_2025.json

# Verify the file was created
ls -lh ../data/raw/
# Expected: ct_bills_2025.json (about 5-10 MB)

# ========================================
# STEP 7: Run Filter Pass
# ========================================
# This processes all bills in batches to identify relevant ones
python run_filter_pass.py

# Expected output (takes 3-5 hours):
# Loading bills from ../data/raw/ct_bills_2025.json
# Processing batch 1/81 (bills 1-50)...
# Processing batch 2/81 (bills 51-100)...
# ...
# Filter complete: 68 relevant, 3996 not relevant
# Saved to: ../data/filtered/filter_results_ct_bills_2025.json

# ========================================
# STEP 8: Run Analysis Pass
# ========================================
# This analyzes the 68 relevant bills with full text
python run_analysis_pass.py

# Expected output (takes 10-15 minutes):
# Loading filter results...
# Found 68 bills to analyze
# Analyzing bill 1/68: SB01071...
# Analyzing bill 2/68: HB05234...
# ...
# Analysis complete: 68 bills analyzed
# Saved to: ../data/analyzed/analysis_results_relevant.json
# Saved to: ../data/analyzed/analysis_results_not_relevant.json

# ========================================
# STEP 9: View Results
# ========================================
cd ..
ls -lh data/analyzed/

# View a sample result
python -c "
import json
with open('data/analyzed/analysis_results_relevant.json') as f:
    bills = json.load(f)
    print(f'✅ Found {len(bills)} relevant bills')
    print(f'First bill: {bills[0][\"bill\"][\"bill_number\"]}')
    print(f'Categories: {bills[0][\"analysis\"][\"categories\"]}')
"

# ========================================
# DONE! 🎉
# ========================================
# Your analyzed bills are in:
# - data/analyzed/analysis_results_relevant.json
# - data/analyzed/analysis_results_not_relevant.json
```

**Total Time:** ~4-6 hours (mostly AI processing)
**Cost:** ~$0.40

---

## Scenario 2: Docker + Azure OpenAI + Local Files

**Goal:** Run pipeline in Docker container using Azure OpenAI while keeping all output files on your local machine.

**What You'll Get:**
- Consistent execution environment (Docker)
- Enterprise-grade AI (Azure OpenAI)
- All data persists on your local machine
- Easy to replicate across machines

**Prerequisites:**
- Docker Desktop installed
- Azure OpenAI resource deployed ([see setup guide](AZURE_OPENAI_SETUP.md))
- LegiScan API key

### Step-by-Step

```bash
# ========================================
# STEP 1: Verify Docker is Running
# ========================================
docker --version
# Expected: Docker version 20.x or higher

docker-compose --version
# Expected: Docker Compose version 2.x or higher

# ========================================
# STEP 2: Clone Repository (if not already done)
# ========================================
cd ~
git clone https://github.com/your-org/ai-scraper-ideas.git
cd ai-scraper-ideas

# ========================================
# STEP 3: Create Environment File
# ========================================
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

# Storage (local files)
STORAGE_BACKEND=local
EOF

# Edit with your actual keys
nano .env

# ========================================
# STEP 4: Create Azure Configuration
# ========================================
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

# ========================================
# STEP 5: Create Data Directories (on local machine)
# ========================================
mkdir -p data/raw
mkdir -p data/filtered
mkdir -p data/analyzed
mkdir -p data/cache/legiscan_cache

# Verify directories exist
ls -la data/
# Expected: raw/, filtered/, analyzed/, cache/

# ========================================
# STEP 6: Build Docker Image
# ========================================
docker-compose build

# Expected output:
# Building legiscan-pipeline
# Step 1/15 : FROM python:3.11-slim AS builder
# ...
# Successfully tagged ai-scraper-ideas_legiscan-pipeline:latest

# ========================================
# STEP 7: Start Container
# ========================================
docker-compose up -d

# Verify container is running
docker-compose ps
# Expected: legiscan-pipeline running

# ========================================
# STEP 8: Test Azure OpenAI Connection
# ========================================
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

# ========================================
# STEP 9: Fetch Bills (inside container)
# ========================================
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# Expected output:
# Fetching bills for state: CT, year: 2025
# Saved to: data/raw/ct_bills_2025.json

# Verify file exists on LOCAL machine
ls -lh data/raw/
# Expected: ct_bills_2025.json (thanks to volume mount!)

# ========================================
# STEP 10: Run Filter Pass (inside container)
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Expected output (3-5 hours):
# Processing batch 1/81...
# ...
# Filter complete: 68 relevant

# Verify results on LOCAL machine
ls -lh data/filtered/
# Expected: filter_results_ct_bills_2025.json

# ========================================
# STEP 11: Run Analysis Pass (inside container)
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# Expected output (10-15 minutes):
# Analyzing bill 1/68...
# ...
# Analysis complete

# Verify results on LOCAL machine
ls -lh data/analyzed/
# Expected: analysis_results_relevant.json, analysis_results_not_relevant.json

# ========================================
# STEP 12: Access Results (from local machine)
# ========================================
# All files are on your local machine in data/
cat data/analyzed/analysis_results_relevant.json | jq '.[0]'

# Or open in your favorite editor
code data/analyzed/analysis_results_relevant.json

# ========================================
# STEP 13: Stop Container (when done)
# ========================================
docker-compose down

# Container is stopped but data remains on your local machine
ls -lh data/analyzed/
# Files still there!

# ========================================
# DONE! 🎉
# ========================================
# Your data is on your local machine in:
# - data/raw/ (LegiScan bills)
# - data/filtered/ (filter results)
# - data/analyzed/ (analyzed bills)
# - data/cache/ (cached API responses)
```

**Key Points:**
- Docker container runs in isolation
- Volume mount (`./data:/app/data`) makes local `data/` directory available inside container
- All output files are written to the mounted volume, appearing on your local machine
- Container can be stopped/started/deleted without losing data

**Total Time:** ~4-6 hours (mostly AI processing)
**Cost:** ~$0.40 + infrastructure

---

## Scenario 3: Docker + Ollama (Zero Cost)

**Goal:** Run entire pipeline locally with no API costs using Ollama.

**What You'll Get:**
- $0 API costs
- Complete data privacy
- No internet dependency (after model download)
- All files stored locally

**Prerequisites:**
- Docker Desktop installed
- Mac M1/M2/M3 with 16GB+ RAM (or Linux with GPU)
- LegiScan API key (for fetching bills)

### Step-by-Step

```bash
# ========================================
# STEP 1: Install Ollama on Host Machine
# ========================================
# For Mac:
curl -fsSL https://ollama.com/install.sh | sh

# For Linux:
curl -fsSL https://ollama.com/install.sh | sh

# For Windows:
# Download from https://ollama.com/download

# Verify installation
ollama --version
# Expected: ollama version 0.x.x

# ========================================
# STEP 2: Pull Llama Model
# ========================================
ollama pull llama3.1:8b-instruct

# This downloads ~4.7GB, may take 5-10 minutes
# Expected output:
# pulling manifest
# pulling 8934d96d3f08... 100%
# success

# Verify model is available
ollama list
# Expected: llama3.1:8b-instruct

# ========================================
# STEP 3: Start Ollama Server
# ========================================
# In a separate terminal (keep running)
ollama serve

# OR run in background
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Verify server is running
curl http://localhost:11434/api/tags
# Expected: JSON response with models

# ========================================
# STEP 4: Clone Repository
# ========================================
cd ~
git clone https://github.com/your-org/ai-scraper-ideas.git
cd ai-scraper-ideas

# ========================================
# STEP 5: Configure for Ollama
# ========================================
cat > .env << 'EOF'
# Ollama Configuration (connecting to host)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b-instruct
LLM_BASE_URL=http://host.docker.internal:11434/v1

# LegiScan Configuration (only external API call)
LEGISCAN_API_KEY=your_legiscan_key_here

# Test Mode (optional)
TEST_MODE=false
TEST_COUNT=5

# Storage
STORAGE_BACKEND=local
EOF

nano .env  # Add your LegiScan API key

# ========================================
# STEP 6: Create Ollama-Friendly Config
# ========================================
cat > config.json << 'EOF'
{
  "llm": {
    "provider": "ollama",
    "model": "llama3.1:8b-instruct",
    "base_url": "http://host.docker.internal:11434/v1"
  },
  "temperature": 0.3,
  "max_tokens": 2000,
  "filter_pass": {
    "batch_size": 10,
    "timeout": 300
  },
  "analysis_pass": {
    "timeout": 180,
    "api_delay": 0.0
  },
  "legiscan": {
    "cache_enabled": true,
    "cache_directory": "data/cache/legiscan_cache"
  }
}
EOF

# ========================================
# STEP 7: Create Override for Docker Compose
# ========================================
cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  legiscan-pipeline:
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_MODEL=${LLM_MODEL}
      - LLM_BASE_URL=${LLM_BASE_URL}
EOF

# ========================================
# STEP 8: Build and Start Container
# ========================================
docker-compose build
docker-compose up -d

# Verify container is running
docker-compose ps

# ========================================
# STEP 9: Test Ollama Connection from Container
# ========================================
docker-compose exec legiscan-pipeline curl http://host.docker.internal:11434/api/tags
# Expected: JSON with available models

# Test with Python
docker-compose exec legiscan-pipeline python -c "
from openai import OpenAI
import os

client = OpenAI(
    base_url='http://host.docker.internal:11434/v1',
    api_key='ollama'  # Ollama doesn't need real key
)

response = client.chat.completions.create(
    model='llama3.1:8b-instruct',
    messages=[{'role': 'user', 'content': 'Say hello in 5 words'}],
    max_tokens=20
)

print('✅ Ollama connection successful!')
print(f'Response: {response.choices[0].message.content}')
"

# ========================================
# STEP 10: Create Data Directories
# ========================================
mkdir -p data/{raw,filtered,analyzed,cache/legiscan_cache}

# ========================================
# STEP 11: Fetch Bills
# ========================================
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# This is the ONLY external API call (LegiScan)
# Expected: data/raw/ct_bills_2025.json

# ========================================
# STEP 12: Run Filter Pass (Local Ollama)
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Expected output (8-10 hours with Ollama):
# Processing batch 1/406... (10 bills per batch with Ollama)
# ...
# Filter complete: 68 relevant

# Monitor progress
docker-compose logs -f legiscan-pipeline

# ========================================
# STEP 13: Run Analysis Pass (Local Ollama)
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# Expected output (30-45 minutes with Ollama):
# Analyzing bill 1/68...
# ...
# Analysis complete

# ========================================
# STEP 14: View Results
# ========================================
ls -lh data/analyzed/

cat data/analyzed/analysis_results_relevant.json | jq '.[0]'

# ========================================
# DONE! 🎉
# ========================================
# Total API cost: $0 (only LegiScan fetching, which is free tier)
# Total time: ~10-12 hours (slower but free!)
# All data stayed on your machine!
```

**Key Points:**
- Ollama runs on host machine for best performance (Metal GPU on Mac)
- Docker container connects to host Ollama via `host.docker.internal`
- No data sent to external APIs (except LegiScan for fetching bills)
- Slower than cloud APIs but completely free

**Total Time:** ~10-12 hours
**Cost:** $0

---

## Scenario 4: Hybrid Approach (Best Value)

**Goal:** Use local Ollama for filter pass (90% of work) and Azure OpenAI for analysis pass (10% of work) to optimize cost vs. quality.

**What You'll Get:**
- 82% cost savings vs. full cloud
- Same quality as full cloud (analysis uses premium API)
- Local data storage

**Prerequisites:**
- Docker Desktop
- Ollama installed
- Azure OpenAI resource
- LegiScan API key

### Step-by-Step

```bash
# ========================================
# STEP 1: Setup Ollama (Same as Scenario 3)
# ========================================
ollama pull llama3.1:8b-instruct
ollama serve &

# ========================================
# STEP 2: Clone and Setup
# ========================================
cd ~
git clone https://github.com/your-org/ai-scraper-ideas.git
cd ai-scraper-ideas

# ========================================
# STEP 3: Create Environment File (Hybrid)
# ========================================
cat > .env << 'EOF'
# Ollama Configuration (for filter pass)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b-instruct
LLM_BASE_URL=http://host.docker.internal:11434/v1

# Azure OpenAI Configuration (for analysis pass)
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# LegiScan
LEGISCAN_API_KEY=your_legiscan_key_here

# Storage
STORAGE_BACKEND=local
EOF

nano .env  # Add your actual keys

# ========================================
# STEP 4: Build and Start Container
# ========================================
docker-compose build
docker-compose up -d

# ========================================
# STEP 5: Fetch Bills
# ========================================
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# ========================================
# STEP 6: Run Filter Pass with Ollama
# ========================================
# Ensure Ollama is being used
docker-compose exec legiscan-pipeline bash -c "
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
export LLM_BASE_URL=http://host.docker.internal:11434/v1
cd scripts && python run_filter_pass.py
"

# Expected: 8-10 hours, $0 cost
# Output: data/filtered/filter_results_ct_bills_2025.json

# ========================================
# STEP 7: Run Analysis Pass with Azure OpenAI
# ========================================
# Switch to Azure OpenAI for higher quality analysis
docker-compose exec legiscan-pipeline bash -c "
export LLM_PROVIDER=azure
export LLM_MODEL=gpt-4o-mini
cd scripts && python run_analysis_pass.py
"

# Expected: 15 minutes, ~$0.07 cost
# Output: data/analyzed/analysis_results_relevant.json

# ========================================
# DONE! 🎉
# ========================================
# Total cost: ~$0.07 (vs $0.37 for full cloud)
# Savings: 82%
# Quality: Same as full cloud (analysis uses Azure)
```

**Total Time:** ~8.5 hours (filter 8h + analysis 0.5h)
**Cost:** ~$0.07

**Cost Breakdown:**
- Filter pass (Ollama): $0
- Analysis pass (Azure OpenAI, 68 bills): ~$0.07
- **Savings: $0.30 (82% reduction)**

---

## Scenario 5: Production Azure Deployment

**Goal:** Deploy pipeline to Azure Container Instances for scheduled production runs.

**What You'll Get:**
- Managed cloud infrastructure
- Scheduled execution
- Persistent storage in Azure Files
- No local machine required

**Prerequisites:**
- Azure subscription
- Azure CLI installed
- Azure OpenAI resource deployed
- LegiScan API key

### Step-by-Step

```bash
# ========================================
# STEP 1: Install Azure CLI
# ========================================
# For Mac:
brew install azure-cli

# For Linux:
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# For Windows:
# Download from https://aka.ms/installazurecliwindows

# Verify installation
az --version

# ========================================
# STEP 2: Login to Azure
# ========================================
az login

# Set subscription (if you have multiple)
az account list --output table
az account set --subscription "Your Subscription Name"

# ========================================
# STEP 3: Create Resource Group
# ========================================
az group create \
  --name rg-legiscan-prod \
  --location eastus

# Verify
az group show --name rg-legiscan-prod

# ========================================
# STEP 4: Create Storage Account
# ========================================
az storage account create \
  --name legiscanstorage \
  --resource-group rg-legiscan-prod \
  --location eastus \
  --sku Standard_LRS

# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group rg-legiscan-prod \
  --account-name legiscanstorage \
  --query "[0].value" -o tsv)

echo "Storage Key: $STORAGE_KEY"

# ========================================
# STEP 5: Create File Share
# ========================================
az storage share create \
  --name legiscan-data \
  --account-name legiscanstorage \
  --account-key "$STORAGE_KEY"

# Verify
az storage share list \
  --account-name legiscanstorage \
  --account-key "$STORAGE_KEY" \
  --output table

# ========================================
# STEP 6: Create Container Registry
# ========================================
az acr create \
  --resource-group rg-legiscan-prod \
  --name legiscanregistry \
  --sku Basic

# Enable admin access
az acr update \
  --name legiscanregistry \
  --admin-enabled true

# Get credentials
ACR_USERNAME=$(az acr credential show \
  --name legiscanregistry \
  --query username -o tsv)

ACR_PASSWORD=$(az acr credential show \
  --name legiscanregistry \
  --query passwords[0].value -o tsv)

echo "Registry: legiscanregistry.azurecr.io"
echo "Username: $ACR_USERNAME"

# ========================================
# STEP 7: Build and Push Docker Image
# ========================================
cd ~/ai-scraper-ideas

# Build and push in one command
az acr build \
  --registry legiscanregistry \
  --image legiscan-pipeline:latest \
  --file Dockerfile .

# Expected output:
# Run ID: ca1 was successful after 2m15s

# Verify image
az acr repository list \
  --name legiscanregistry \
  --output table

# ========================================
# STEP 8: Deploy Container Instance
# ========================================
az container create \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --cpu 4 \
  --memory 8 \
  --registry-login-server legiscanregistry.azurecr.io \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --environment-variables \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" \
    LEGISCAN_API_KEY="$LEGISCAN_API_KEY" \
    STORAGE_BACKEND=local \
  --azure-file-volume-account-name legiscanstorage \
  --azure-file-volume-account-key "$STORAGE_KEY" \
  --azure-file-volume-share-name legiscan-data \
  --azure-file-volume-mount-path /app/data

# Expected output (takes 2-3 minutes):
# Container 'legiscan-pipeline' created successfully

# ========================================
# STEP 9: Verify Container is Running
# ========================================
az container show \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --query "provisioningState" -o tsv

# Expected: Succeeded

# ========================================
# STEP 10: Run Pipeline Commands
# ========================================
# Fetch bills
az container exec \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --exec-command "python scripts/fetch_legiscan_bills.py"

# Run filter pass
az container exec \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --exec-command "bash -c 'cd scripts && python run_filter_pass.py'"

# Run analysis pass
az container exec \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --exec-command "bash -c 'cd scripts && python run_analysis_pass.py'"

# ========================================
# STEP 11: View Logs
# ========================================
az container logs \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline

# Or stream logs
az container attach \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline

# ========================================
# STEP 12: Download Results to Local Machine
# ========================================
# Install Azure Storage Explorer or use CLI

# List files in Azure File Share
az storage file list \
  --account-name legiscanstorage \
  --account-key "$STORAGE_KEY" \
  --share-name legiscan-data \
  --path analyzed \
  --output table

# Download specific file
az storage file download \
  --account-name legiscanstorage \
  --account-key "$STORAGE_KEY" \
  --share-name legiscan-data \
  --path analyzed/analysis_results_relevant.json \
  --dest ~/Downloads/analysis_results_relevant.json

# ========================================
# STEP 13: Cleanup (when done)
# ========================================
# Stop container (keeps data)
az container stop \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline

# Delete container (keeps data in file share)
az container delete \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --yes

# Delete entire resource group (deletes EVERYTHING)
# az group delete --name rg-legiscan-prod --yes

# ========================================
# DONE! 🎉
# ========================================
```

**Total Time:** 3-4 hours (first time), 30 minutes (subsequent deploys)
**Cost:** ~$0.40 API + ~$30/month infrastructure

---

## Scenario 6: Multiple States Processing

**Goal:** Process bills from multiple states in parallel.

**What You'll Get:**
- Bills from CT, NY, CA, TX, and FL
- Parallel processing
- Combined analysis results

### Step-by-Step

```bash
# ========================================
# STEP 1: Setup (Use any environment from previous scenarios)
# ========================================
# For this example, using Docker + Azure OpenAI
docker-compose up -d

# ========================================
# STEP 2: Modify Fetch Script for Multiple States
# ========================================
cat > scripts/fetch_multiple_states.sh << 'EOF'
#!/bin/bash

STATES=("CT" "NY" "CA" "TX" "FL")

for STATE in "${STATES[@]}"; do
  echo "Fetching bills for $STATE..."
  python fetch_legiscan_bills.py --state "$STATE" --year 2025
done

echo "All states fetched!"
EOF

chmod +x scripts/fetch_multiple_states.sh

# ========================================
# STEP 3: Fetch Bills for All States
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && bash fetch_multiple_states.sh"

# Verify files
docker-compose exec legiscan-pipeline ls -lh data/raw/
# Expected: ct_bills_2025.json, ny_bills_2025.json, etc.

# ========================================
# STEP 4: Create Filter Script for Multiple States
# ========================================
cat > scripts/filter_multiple_states.sh << 'EOF'
#!/bin/bash

for STATE_FILE in ../data/raw/*_bills_2025.json; do
  BASENAME=$(basename "$STATE_FILE" .json)
  echo "Filtering $BASENAME..."
  python run_filter_pass.py "$BASENAME" &
done

wait
echo "All filters complete!"
EOF

chmod +x scripts/filter_multiple_states.sh

# ========================================
# STEP 5: Run Filter Pass for All States (Parallel)
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && bash filter_multiple_states.sh"

# This runs all states in parallel!
# Monitor progress
docker-compose logs -f legiscan-pipeline

# Verify results
docker-compose exec legiscan-pipeline ls -lh data/filtered/
# Expected: filter_results_ct_bills_2025.json, filter_results_ny_bills_2025.json, etc.

# ========================================
# STEP 6: Run Analysis Pass (Processes All States)
# ========================================
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# This automatically finds and processes ALL filter results
# Output will be combined into single files with state information

# ========================================
# STEP 7: View Combined Results
# ========================================
docker-compose exec legiscan-pipeline python -c "
import json

with open('data/analyzed/analysis_results_relevant.json') as f:
    bills = json.load(f)

# Count by state
from collections import Counter
states = [b.get('bill', {}).get('state', 'Unknown') for b in bills]
state_counts = Counter(states)

print(f'Total bills: {len(bills)}')
print('By state:')
for state, count in state_counts.most_common():
    print(f'  {state}: {count}')
"

# ========================================
# DONE! 🎉
# ========================================
```

**Total Time:** ~15-20 hours (parallel processing helps but limited by API rate limits)
**Cost:** ~$2-5 depending on total bills

---

## Scenario 7: LegiUI Dashboard Setup

**Goal:** Set up the React dashboard to visualize analysis results.

**What You'll Get:**
- Interactive web dashboard
- Filter and search bills
- Visualizations by state, category, year
- Detailed bill views

### Step-by-Step

```bash
# ========================================
# STEP 1: Verify You Have Analysis Results
# ========================================
ls -lh data/analyzed/
# Expected: analysis_results_relevant.json

# ========================================
# STEP 2: Navigate to LegiUI Directory
# ========================================
cd legiUI

# ========================================
# STEP 3: Install Node.js Dependencies
# ========================================
npm install

# Expected output:
# added 250 packages in 15s

# ========================================
# STEP 4: Load Data from Analysis Results
# ========================================
npm run load-data

# Expected output:
# Loading analysis data from ../data/analyzed/
# Found 2 result files
# Loaded 68 bills from filter_results_ct_bills_2025_relevant.json
# Combined 68 bills total
# Saved to public/bills.json

# ========================================
# STEP 5: Start Development Server
# ========================================
npm run dev

# Expected output:
#   VITE v5.0.0  ready in 500 ms
#
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose

# ========================================
# STEP 6: Open in Browser
# ========================================
open http://localhost:5173

# Or manually navigate to http://localhost:5173

# ========================================
# STEP 7: Explore Dashboard
# ========================================
# You should see:
# - Total bills count
# - Filters for state, category, year, status
# - Search box
# - Charts showing distribution
# - Table of bills
# - Click any bill to see details

# ========================================
# STEP 8: Build for Production (Optional)
# ========================================
npm run build

# Creates optimized production build in dist/
# Output: dist/index.html, dist/assets/*

# Preview production build
npm run preview
open http://localhost:4173

# ========================================
# STEP 9: Deploy to GitHub Pages (Optional)
# ========================================
# See main README for GitHub Pages deployment instructions

# ========================================
# DONE! 🎉
# ========================================
# Dashboard is running at http://localhost:5173
# Press Ctrl+C to stop
```

**Total Time:** 5-10 minutes
**Cost:** $0 (runs locally)

---

## Scenario 8: Testing with 5 Bills

**Goal:** Test the entire pipeline with just 5 bills before running on full dataset.

**What You'll Get:**
- Quick validation (minutes instead of hours)
- Verify configuration is correct
- Check output format
- No significant API costs

### Step-by-Step

```bash
# ========================================
# Works with ANY environment (Local, Docker, Azure)
# ========================================

# ========================================
# STEP 1: Enable Test Mode
# ========================================
# Add to .env file
cat >> .env << 'EOF'

# Test Mode
TEST_MODE=true
TEST_COUNT=5
EOF

# Or set as environment variables
export TEST_MODE=true
export TEST_COUNT=5

# ========================================
# STEP 2: Restart Container (if using Docker)
# ========================================
docker-compose restart

# ========================================
# STEP 3: Fetch Bills (Full Dataset Still Needed)
# ========================================
# Fetch full dataset first
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py

# Or if local:
cd scripts
python fetch_legiscan_bills.py

# ========================================
# STEP 4: Run Filter Pass (Only 5 Bills)
# ========================================
# Docker:
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Local:
cd scripts
python run_filter_pass.py

# Expected output (takes ~30 seconds):
# TEST MODE: Processing only 5 bills
# Loading bills from ../data/raw/ct_bills_2025.json
# Selected 5 test bills
# Processing batch 1/1 (5 bills)...
# Filter complete: 2 relevant, 3 not relevant

# ========================================
# STEP 5: Run Analysis Pass (Only Relevant from Test)
# ========================================
# Docker:
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# Local:
python run_analysis_pass.py

# Expected output (takes ~1 minute):
# TEST MODE: Processing only 5 bills from filter results
# Analyzing bill 1/2...
# Analyzing bill 2/2...
# Analysis complete

# ========================================
# STEP 6: Verify Results
# ========================================
cat data/analyzed/analysis_results_relevant.json | jq '.'

# Expected: 1-2 bills with full analysis

# ========================================
# STEP 7: Disable Test Mode for Production Run
# ========================================
# Remove from .env
sed -i '' '/TEST_MODE/d' .env

# Or unset variables
unset TEST_MODE
unset TEST_COUNT

# Restart container
docker-compose restart

# ========================================
# STEP 8: Run Full Pipeline
# ========================================
# Now run with full dataset
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# ========================================
# DONE! 🎉
# ========================================
```

**Total Time:** 2-3 minutes
**Cost:** < $0.01

---

## Quick Reference

| Scenario | Environment | LLM | Time | Cost | Use Case |
|----------|-------------|-----|------|------|----------|
| 1 | Local Native | Portkey | ~4h | $0.40 | First-time testing |
| 2 | Docker | Azure OpenAI | ~4h | $0.40 | Your specific request! |
| 3 | Docker | Ollama | ~10h | $0 | Zero cost |
| 4 | Docker | Hybrid | ~8h | $0.07 | Best value |
| 5 | Azure | Azure OpenAI | ~3h | $0.40 + infra | Production |
| 6 | Any | Any | ~15h | Varies | Multiple states |
| 7 | Local | N/A | 5min | $0 | Dashboard |
| 8 | Any | Any | 2min | <$0.01 | Testing |

---

**Need Help?**
- Full environment details: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Docker specifics: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- Azure setup: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- Local LLM: [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team
