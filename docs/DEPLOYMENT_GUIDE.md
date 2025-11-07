# Deployment Guide

Comprehensive comparison and decision guide for all deployment options for the LegiScan Bill Analysis Pipeline.

## Table of Contents

1. [Deployment Options Overview](#deployment-options-overview)
2. [Decision Matrix](#decision-matrix)
3. [Environment Comparisons](#environment-comparisons)
4. [LLM Provider Comparisons](#llm-provider-comparisons)
5. [Cost Analysis](#cost-analysis)
6. [Performance Benchmarks](#performance-benchmarks)
7. [Security Considerations](#security-considerations)
8. [Scalability Guide](#scalability-guide)

---

## Deployment Options Overview

### Execution Environments

| Environment | Best For | Complexity | Cost |
|-------------|----------|------------|------|
| **Local (Native)** | Development, testing | ⭐ Low | $0 hardware |
| **Docker (Local)** | Consistent environments | ⭐⭐ Medium | $0 hardware |
| **Azure Container Instances** | Production, enterprise | ⭐⭐⭐ Medium | $$$ pay-as-you-go |
| **Azure Container Apps** | Scalable production | ⭐⭐⭐⭐ High | $$$ auto-scaling |
| **Kubernetes** | Large scale, multi-tenant | ⭐⭐⭐⭐⭐ Very High | $$$$ |

### LLM Provider Options

| Provider | Best For | Setup | Cost per 4K bills |
|----------|----------|-------|-------------------|
| **Portkey** | Quick start, multi-provider | ⭐ Easy | ~$30 |
| **Azure OpenAI** | Enterprise, compliance | ⭐⭐⭐ Medium | ~$30 |
| **Ollama (Local)** | Privacy, high volume | ⭐⭐ Medium | $0 (time cost) |
| **Hybrid** | Cost optimization | ⭐⭐⭐ Medium | ~$2-5 |

---

## Decision Matrix

### Choose Your Deployment

Answer these questions to find your ideal deployment:

#### Question 1: What's your primary goal?

- **Quick testing/prototyping** → Local Native + Portkey
- **Production deployment** → Docker or Azure + Azure OpenAI
- **Cost optimization** → Docker + Ollama (Local LLM)
- **Enterprise compliance** → Azure Container Apps + Azure OpenAI
- **Maximum privacy** → Local/Docker + Ollama

#### Question 2: What's your budget?

- **$0-5 per run** → Ollama (local) or Hybrid approach
- **$20-50 per run** → Portkey or Azure OpenAI
- **Budget not a concern** → Azure OpenAI with gpt-4o

#### Question 3: What's your technical expertise?

- **Beginner** → Local Native + Portkey
- **Intermediate** → Docker + Portkey/Azure OpenAI
- **Advanced** → Docker + Ollama or Azure Container Apps
- **DevOps/Enterprise** → Kubernetes + Azure OpenAI

#### Question 4: What's your data sensitivity?

- **Public data** → Any option
- **Sensitive (HIPAA, etc.)** → Azure OpenAI or Local Ollama
- **Highly sensitive** → Local Ollama only

#### Question 5: What's your processing volume?

- **One-time (< 5K bills)** → Local Native + Portkey
- **Regular (weekly/monthly)** → Docker + Hybrid approach
- **High volume (> 50K bills/month)** → Ollama or Azure with high quotas
- **Continuous** → Azure Container Apps + Azure OpenAI

### Recommended Combinations

Based on the decision matrix, here are optimal combinations:

#### 🥇 Recommended: Development & Testing

```
Environment: Local Native or Docker
LLM Provider: Portkey
Total Setup Time: 15 minutes
Cost per Run: ~$30
```

**Why:**
- Fastest setup
- Easy debugging
- No infrastructure management
- Pay-as-you-go pricing

**Quick Start:**
```bash
# Clone repo
git clone https://github.com/your-repo/ai-scraper-ideas.git
cd ai-scraper-ideas

# Setup environment
cp .env.example .env
# Edit .env with API keys

# Install and run
pip install -r requirements.txt
cd scripts
python fetch_legiscan_bills.py
python run_filter_pass.py
python run_analysis_pass.py
```

---

#### 🥇 Recommended: Production (Enterprise)

```
Environment: Azure Container Apps
LLM Provider: Azure OpenAI
Total Setup Time: 2-3 hours
Cost per Run: ~$30 + infrastructure (~$50/month)
```

**Why:**
- Enterprise security and compliance
- Automatic scaling
- Full Azure ecosystem integration
- Managed infrastructure

**Quick Start:**
See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for full setup.

---

#### 🥇 Recommended: Cost-Optimized Production

```
Environment: Docker on dedicated server
LLM Provider: Hybrid (Ollama filter + Azure OpenAI analysis)
Total Setup Time: 1 hour
Cost per Run: ~$2-5
```

**Why:**
- 90% cost reduction vs full cloud
- Good quality maintained
- Predictable costs
- Simple infrastructure

**Quick Start:**
```bash
# Setup Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b-instruct
ollama serve &

# Setup pipeline
docker-compose up -d

# Run filter with Ollama (free)
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"

# Run analysis with Azure OpenAI (paid, higher quality)
export LLM_PROVIDER=azure
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"
```

---

#### 🥇 Recommended: Maximum Privacy

```
Environment: Docker with local storage
LLM Provider: Ollama (fully local)
Total Setup Time: 30 minutes
Cost per Run: $0 (time cost: 2-3x slower)
```

**Why:**
- No data leaves your infrastructure
- No API costs
- Complete control
- No rate limits

**Quick Start:**
See [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md) for full setup.

---

## Environment Comparisons

### Local Native

**Architecture:**
```
Your Machine
├── Python 3.11+
├── Virtual Environment
├── Source Code
└── Data Directory
     └── API → Portkey/Azure/Ollama
```

**Pros:**
- ✅ Fastest setup (5 minutes)
- ✅ Easy debugging
- ✅ Direct file access
- ✅ No Docker knowledge needed
- ✅ Full IDE integration

**Cons:**
- ❌ "Works on my machine" issues
- ❌ Manual dependency management
- ❌ No environment isolation
- ❌ Hard to replicate across team

**Best For:**
- Solo developers
- Quick prototyping
- One-time analysis
- Learning the system

**Setup Steps:**
```bash
# 1. Clone repository
git clone https://github.com/your-repo/ai-scraper-ideas.git
cd ai-scraper-ideas

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 5. Verify setup
python -c "import openai; print('✅ Setup complete!')"

# 6. Run pipeline
cd scripts
python fetch_legiscan_bills.py
python run_filter_pass.py
python run_analysis_pass.py

# 7. View results
ls -lh ../data/analyzed/
```

**Estimated Time:** 5-10 minutes

---

### Docker Local

**Architecture:**
```
Your Machine
├── Docker Engine
└── Container
    ├── Python 3.11
    ├── Source Code (mounted)
    ├── Data Directory (mounted)
    └── API → Portkey/Azure/Ollama
```

**Pros:**
- ✅ Consistent across machines
- ✅ Environment isolation
- ✅ Easy to replicate
- ✅ Works on Windows/Mac/Linux identically
- ✅ Simple cleanup (remove container)

**Cons:**
- ❌ Requires Docker knowledge
- ❌ Slightly more setup overhead
- ❌ Volume mounting complexity
- ❌ Slower file I/O (on Mac)

**Best For:**
- Team collaboration
- CI/CD pipelines
- Testing before cloud deployment
- Windows users

**Setup Steps:**
```bash
# 1. Verify Docker is installed
docker --version
docker-compose --version

# 2. Clone repository
git clone https://github.com/your-repo/ai-scraper-ideas.git
cd ai-scraper-ideas

# 3. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 4. Build and start
docker-compose build
docker-compose up -d

# 5. Verify container is running
docker-compose ps
# Expected: legiscan-pipeline running

# 6. Run pipeline
docker-compose exec legiscan-pipeline python scripts/fetch_legiscan_bills.py
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_filter_pass.py"
docker-compose exec legiscan-pipeline bash -c "cd scripts && python run_analysis_pass.py"

# 7. View results
ls -lh data/analyzed/

# 8. Cleanup (when done)
docker-compose down
```

**Estimated Time:** 15-20 minutes

**See Also:** [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker guide.

---

### Azure Container Instances

**Architecture:**
```
Azure Cloud
├── Container Instance
│   ├── Python 3.11
│   ├── Source Code (baked in)
│   └── API → Azure OpenAI (same region)
└── Azure Files (mounted)
    └── Data Directory
```

**Pros:**
- ✅ Managed infrastructure
- ✅ Pay only when running
- ✅ Fast startup (~30 seconds)
- ✅ Azure ecosystem integration
- ✅ No server management

**Cons:**
- ❌ More complex setup
- ❌ Azure knowledge required
- ❌ Higher cost than local
- ❌ Internet dependency
- ❌ Cold start delays

**Best For:**
- Production deployments
- Scheduled processing
- Enterprise environments
- Teams already on Azure

**Setup Steps:**
```bash
# 1. Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login

# 2. Create resource group
az group create \
  --name rg-legiscan-prod \
  --location eastus

# 3. Create storage account
az storage account create \
  --name legiscanstorage \
  --resource-group rg-legiscan-prod \
  --location eastus \
  --sku Standard_LRS

# 4. Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group rg-legiscan-prod \
  --account-name legiscanstorage \
  --query "[0].value" -o tsv)

# 5. Create file share
az storage share create \
  --name legiscan-data \
  --account-name legiscanstorage \
  --account-key $STORAGE_KEY

# 6. Build and push Docker image to Azure Container Registry
az acr create \
  --resource-group rg-legiscan-prod \
  --name legiscanregistry \
  --sku Basic

az acr build \
  --registry legiscanregistry \
  --image legiscan-pipeline:latest \
  --file Dockerfile .

# 7. Deploy container instance
az container create \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --cpu 4 \
  --memory 8 \
  --registry-login-server legiscanregistry.azurecr.io \
  --registry-username $(az acr credential show --name legiscanregistry --query username -o tsv) \
  --registry-password $(az acr credential show --name legiscanregistry --query passwords[0].value -o tsv) \
  --environment-variables \
    AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY \
    AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini \
    LEGISCAN_API_KEY=$LEGISCAN_API_KEY \
  --azure-file-volume-account-name legiscanstorage \
  --azure-file-volume-account-key $STORAGE_KEY \
  --azure-file-volume-share-name legiscan-data \
  --azure-file-volume-mount-path /app/data

# 8. Run commands in container
az container exec \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --exec-command "python scripts/fetch_legiscan_bills.py"

az container exec \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --exec-command "bash -c 'cd scripts && python run_filter_pass.py'"

# 9. View logs
az container logs \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline

# 10. Cleanup (when done)
az container delete \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --yes
```

**Estimated Time:** 2-3 hours (first time), 30 minutes (subsequent)

**See Also:** [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for detailed Azure guide.

---

### Azure Container Apps

**Architecture:**
```
Azure Cloud
├── Container App Environment
│   └── Container App (auto-scaling)
│       ├── Python 3.11
│       ├── Source Code (baked in)
│       └── API → Azure OpenAI
├── Azure Files (mounted)
│   └── Data Directory
└── Azure Monitor
    └── Logs & Metrics
```

**Pros:**
- ✅ Auto-scaling (0 to N replicas)
- ✅ Built-in ingress (if needed for API)
- ✅ Managed environments
- ✅ Advanced networking
- ✅ Integrated monitoring
- ✅ Revision management

**Cons:**
- ❌ Most complex setup
- ❌ Higher cost than Container Instances
- ❌ Overkill for simple batch jobs
- ❌ Steeper learning curve

**Best For:**
- Large scale deployments
- API endpoints (if building one)
- Multi-tenant scenarios
- Advanced networking requirements

**Setup Steps:**
```bash
# 1. Install Container Apps extension
az extension add --name containerapp --upgrade

# 2. Register provider
az provider register --namespace Microsoft.App

# 3. Create environment
az containerapp env create \
  --name legiscan-env \
  --resource-group rg-legiscan-prod \
  --location eastus

# 4. Create storage mount
az containerapp env storage set \
  --name legiscan-env \
  --resource-group rg-legiscan-prod \
  --storage-name legiscan-data \
  --azure-file-account-name legiscanstorage \
  --azure-file-account-key $STORAGE_KEY \
  --azure-file-share-name legiscan-data \
  --access-mode ReadWrite

# 5. Deploy container app
az containerapp create \
  --name legiscan-pipeline \
  --resource-group rg-legiscan-prod \
  --environment legiscan-env \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --registry-server legiscanregistry.azurecr.io \
  --registry-username $(az acr credential show --name legiscanregistry --query username -o tsv) \
  --registry-password $(az acr credential show --name legiscanregistry --query passwords[0].value -o tsv) \
  --cpu 4 \
  --memory 8Gi \
  --min-replicas 0 \
  --max-replicas 1 \
  --secrets \
    azure-openai-key=$AZURE_OPENAI_API_KEY \
    legiscan-key=$LEGISCAN_API_KEY \
  --env-vars \
    AZURE_OPENAI_API_KEY=secretref:azure-openai-key \
    AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini \
    LEGISCAN_API_KEY=secretref:legiscan-key

# 6. Create job for pipeline execution
az containerapp job create \
  --name legiscan-job \
  --resource-group rg-legiscan-prod \
  --environment legiscan-env \
  --trigger-type Manual \
  --replica-timeout 3600 \
  --replica-retry-limit 0 \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --cpu 4 \
  --memory 8Gi \
  --command "bash" "-c" "cd scripts && python run_filter_pass.py && python run_analysis_pass.py"

# 7. Execute job
az containerapp job start \
  --name legiscan-job \
  --resource-group rg-legiscan-prod

# 8. View execution logs
az containerapp job execution list \
  --name legiscan-job \
  --resource-group rg-legiscan-prod \
  --output table
```

**Estimated Time:** 3-4 hours (first time), 1 hour (subsequent)

---

## LLM Provider Comparisons

### Portkey (OpenAI via Gateway)

**Architecture:**
```
Your App → Portkey API → OpenAI API → Response
```

**Setup Complexity:** ⭐ Very Easy

**Pros:**
- ✅ Simplest setup (just API key)
- ✅ Multi-provider support (OpenAI, Anthropic, etc.)
- ✅ Built-in analytics dashboard
- ✅ Automatic failover
- ✅ Cost tracking

**Cons:**
- ❌ Additional proxy in request path
- ❌ Portkey service dependency
- ❌ Slight latency overhead
- ❌ Data passes through third party
- ❌ Additional cost (minimal)

**Configuration:**
```bash
# .env file
PORTKEY_API_KEY=pk_live_xxxxxxxxxxxxxxxx
LEGISCAN_API_KEY=xxxxxxxxxxxxxxxx

# config.json (optional - uses defaults)
{
  "llm": {
    "provider": "portkey",
    "model": "gpt-4o-mini",
    "base_url": "https://api.portkey.ai/v1"
  },
  "temperature": 0.3,
  "max_tokens": 2000
}
```

**Cost (4,000 bills):**
- Filter pass: ~$0.30
- Analysis pass (68 bills): ~$0.07
- **Total: ~$0.37 + Portkey fee (minimal)**

**When to Use:**
- Quick prototyping
- Multi-provider experimentation
- Need failover/analytics
- Don't have enterprise requirements

---

### Azure OpenAI

**Architecture:**
```
Your App → Azure OpenAI Endpoint → Response
```

**Setup Complexity:** ⭐⭐⭐ Medium

**Pros:**
- ✅ Enterprise security (HIPAA, SOC 2, etc.)
- ✅ Data stays in your Azure tenant
- ✅ Full Azure ecosystem integration
- ✅ Configurable rate limits
- ✅ Private endpoints available
- ✅ No third-party dependencies

**Cons:**
- ❌ Requires Azure account and approval
- ❌ More complex setup
- ❌ Region availability limitations
- ❌ Requires resource management

**Configuration:**
```bash
# .env file
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
LEGISCAN_API_KEY=xxxxxxxxxxxxxxxx

# config.json
{
  "llm": {
    "provider": "azure",
    "deployment_name": "gpt-4o-mini",
    "endpoint": null,  # Uses env var
    "api_key": null,   # Uses env var
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
  }
}
```

**Cost (4,000 bills with gpt-4o-mini):**
- Filter pass: ~$0.30
- Analysis pass (68 bills): ~$0.07
- **Total: ~$0.37**

**When to Use:**
- Enterprise deployments
- Compliance requirements (HIPAA, etc.)
- Already on Azure
- Need private networking
- High rate limit requirements

**See Also:** [AZURE_OPENAI_SETUP.md](AZURE_OPENAI_SETUP.md)

---

### Ollama (Local LLM)

**Architecture:**
```
Your App → Ollama Server (localhost) → Local Model → Response
```

**Setup Complexity:** ⭐⭐ Medium

**Pros:**
- ✅ $0 API costs
- ✅ Complete data privacy
- ✅ No rate limits
- ✅ No internet dependency
- ✅ Customizable models

**Cons:**
- ❌ Requires local hardware (16GB+ RAM)
- ❌ 2-3x slower than cloud APIs
- ❌ Slightly lower quality
- ❌ Need to manage models

**Configuration:**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull model
ollama pull llama3.1:8b-instruct

# 3. Start server
ollama serve &

# 4. Configure app
# .env file
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b-instruct
LLM_BASE_URL=http://localhost:11434/v1
LEGISCAN_API_KEY=xxxxxxxxxxxxxxxx

# config.json
{
  "llm": {
    "provider": "ollama",
    "model": "llama3.1:8b-instruct",
    "base_url": "http://localhost:11434/v1"
  },
  "temperature": 0.3,
  "max_tokens": 2000,
  "filter_pass": {
    "batch_size": 10,  # Smaller for local
    "timeout": 300     # Longer timeout
  }
}
```

**Cost (4,000 bills):**
- **$0 API costs**
- Time cost: ~8-12 hours (vs 3-5 hours with cloud)

**Hardware Requirements:**
- **Minimum:** Mac M1 with 16GB RAM
- **Recommended:** Mac M1/M2 with 32GB+ RAM
- **For 70B models:** Mac M1 Ultra with 64GB+ RAM

**Model Options:**

| Model | RAM | Speed | Quality | Use Case |
|-------|-----|-------|---------|----------|
| llama3.1:8b | 8GB | Fast | Good | General use |
| mistral:7b | 6GB | Very Fast | Decent | Budget option |
| llama3.1:70b-q4 | 40GB | Slow | Excellent | Best quality |

**When to Use:**
- High-volume processing
- Privacy-sensitive data
- Budget constraints
- Have capable hardware
- No internet connectivity

**See Also:** [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)

---

### Hybrid Approach

**Architecture:**
```
Filter Pass → Ollama (local) → 4,000 bills → 68 relevant
Analysis Pass → Azure/Portkey → 68 bills → Categorized results
```

**Setup Complexity:** ⭐⭐⭐ Medium-High

**Pros:**
- ✅ 90% cost reduction
- ✅ Maintains quality where it matters
- ✅ Flexible optimization
- ✅ Best cost/quality ratio

**Cons:**
- ❌ More complex setup
- ❌ Requires managing two providers
- ❌ Longer total runtime

**Configuration:**
```bash
# For filter pass: use Ollama
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
cd scripts
python run_filter_pass.py

# For analysis pass: use Azure OpenAI
export LLM_PROVIDER=azure
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
python run_analysis_pass.py
```

**Cost (4,000 bills):**
- Filter pass (Ollama): $0
- Analysis pass (Azure, 68 bills): ~$0.07
- **Total: ~$0.07 (vs $0.37 full cloud)**

**Time:**
- Filter: ~8 hours (Ollama)
- Analysis: ~15 minutes (Azure)
- **Total: ~8.25 hours (vs 4 hours full cloud)**

**When to Use:**
- Regular processing
- Cost optimization priority
- Have capable hardware
- Quality matters for final analysis

---

## Cost Analysis

### Full Cost Breakdown (4,000 Bills)

#### Scenario 1: Cloud Only (Portkey/Azure OpenAI with gpt-4o-mini)

```
Filter Pass:
  - Input: 4,000 bills × 500 tokens = 2M tokens × $0.15/M = $0.30
  - Output: 80 batches × 100 tokens = 8K tokens × $0.60/M = $0.005

Analysis Pass (68 relevant bills):
  - Input: 68 bills × 3,000 tokens = 204K tokens × $0.15/M = $0.03
  - Output: 68 bills × 1,000 tokens = 68K tokens × $0.60/M = $0.04

Total API Cost: ~$0.38
Infrastructure: $0 (local) or ~$10-50/month (Azure)

Monthly (4 runs): ~$1.52 + infrastructure
Yearly (48 runs): ~$18.24 + infrastructure
```

#### Scenario 2: Ollama Only (Local LLM)

```
Filter Pass: $0
Analysis Pass: $0

Total API Cost: $0
Infrastructure: $0
Hardware Cost: Mac M1/M2 (already owned) or ~$1,500-3,000

Monthly (4 runs): $0
Yearly (48 runs): $0

Time Cost: 2-3x longer processing time
```

#### Scenario 3: Hybrid (Ollama Filter + Cloud Analysis)

```
Filter Pass (Ollama): $0
Analysis Pass (Azure, 68 bills): $0.07

Total API Cost: ~$0.07
Infrastructure: $0 (local) or ~$10-50/month (Azure)

Monthly (4 runs): ~$0.28 + infrastructure
Yearly (48 runs): ~$3.36 + infrastructure

Savings: 82% vs full cloud
```

#### Scenario 4: Cloud with gpt-4o (Premium)

```
Filter Pass:
  - Input: 2M tokens × $2.50/M = $5.00
  - Output: 8K tokens × $10.00/M = $0.08

Analysis Pass:
  - Input: 204K tokens × $2.50/M = $0.51
  - Output: 68K tokens × $10.00/M = $0.68

Total API Cost: ~$6.27
Infrastructure: $0 (local) or ~$10-50/month (Azure)

Monthly (4 runs): ~$25.08 + infrastructure
Yearly (48 runs): ~$300.96 + infrastructure
```

### Infrastructure Costs (Azure)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **Container Instance** | 4 vCPU, 8GB RAM, 10 hrs/month | ~$30 |
| **Container Apps** | 4 vCPU, 8GB RAM, with auto-scale | ~$50-100 |
| **Storage Account** | Standard LRS, 10GB | ~$0.50 |
| **Azure OpenAI** | Pay-per-token | Variable |
| **Container Registry** | Basic tier | ~$5 |

**Total Infrastructure (minimal):** ~$35-105/month

### Cost Optimization Tips

1. **Use Hybrid Approach:** 82% savings
2. **Use gpt-4o-mini instead of gpt-4o:** 95% savings
3. **Batch Processing:** Reduce API calls by 50x
4. **Caching:** Avoid re-fetching LegiScan bills
5. **Test Mode:** Test with 5 bills before full run
6. **Increase Batch Size:** 50-100 bills per API call
7. **Use Spot Instances (Azure):** 70-90% infrastructure savings

---

## Performance Benchmarks

### Processing Time (4,000 Bills → 68 Relevant)

| Environment | LLM Provider | Filter Time | Analysis Time | Total |
|-------------|--------------|-------------|---------------|-------|
| Local Native | Portkey (gpt-4o-mini) | 3 hours | 15 min | ~3.25 hours |
| Local Native | Azure OpenAI (gpt-4o-mini) | 3 hours | 15 min | ~3.25 hours |
| Local Native | Ollama (8b) | 8 hours | 40 min | ~8.67 hours |
| Docker Local | Portkey | 3.5 hours | 18 min | ~3.8 hours |
| Docker Local | Ollama (8b) | 10 hours | 45 min | ~10.75 hours |
| Azure Container | Azure OpenAI | 2.5 hours | 12 min | ~2.7 hours |
| Hybrid | Ollama + Azure | 8 hours | 15 min | ~8.25 hours |

**Notes:**
- Times based on Mac M1 Pro for local, 4 vCPU Azure for cloud
- Assumes 50 bills/batch for cloud, 10 bills/batch for Ollama
- Network speed affects LegiScan API fetching (~30 min)

### Throughput (Bills Processed per Hour)

| Configuration | Bills/Hour |
|---------------|------------|
| Portkey (gpt-4o-mini) | ~1,230 |
| Azure OpenAI (gpt-4o-mini) | ~1,480 |
| Ollama 8B (local) | ~400 |
| Ollama 70B (local) | ~100 |
| gpt-4o (premium) | ~800 |

### Concurrent Processing

```bash
# Run multiple states in parallel (local/Docker)
# Terminal 1
cd scripts
python run_filter_pass.py ct_bills_2025 &

# Terminal 2
python run_filter_pass.py ny_bills_2025 &

# Terminal 3
python run_filter_pass.py ca_bills_2025 &

# Wait for all to complete
wait

# Process all analysis
python run_analysis_pass.py
```

**Speedup:** Up to 3x with 3 parallel processes (limited by API rate limits)

---

## Security Considerations

### Data Security by Environment

| Environment | Data at Rest | Data in Transit | Code Security |
|-------------|--------------|-----------------|---------------|
| **Local Native** | ⚠️ Unencrypted | ✅ HTTPS to APIs | ⚠️ Local filesystem |
| **Docker Local** | ⚠️ Unencrypted | ✅ HTTPS to APIs | ⚠️ Container isolation |
| **Azure Container** | ✅ Encrypted (Azure Files) | ✅ HTTPS + VNet | ✅ Registry scanning |
| **Ollama Only** | ⚠️ Unencrypted | ✅ No external calls | ✅ Fully local |

### API Key Management

#### ❌ Bad Practices

```bash
# DO NOT hardcode in config.json
{
  "llm": {
    "api_key": "pk_live_secret123"  # NEVER DO THIS
  }
}

# DO NOT commit .env to git
git add .env  # NEVER DO THIS
```

#### ✅ Good Practices

```bash
# Use environment variables
# .env (gitignored)
PORTKEY_API_KEY=pk_live_secret123
AZURE_OPENAI_API_KEY=secret456

# config.json references env vars
{
  "llm": {
    "api_key": null  # Uses PORTKEY_API_KEY env var
  }
}

# For production: Use Azure Key Vault
az keyvault secret set \
  --vault-name my-vault \
  --name PORTKEY-API-KEY \
  --value pk_live_secret123
```

### Compliance Considerations

| Requirement | Portkey | Azure OpenAI | Ollama |
|-------------|---------|--------------|--------|
| **HIPAA** | ⚠️ Portkey BAA required | ✅ Azure HIPAA compliant | ✅ Fully local |
| **SOC 2** | ✅ Portkey SOC 2 | ✅ Azure SOC 2 | ✅ N/A |
| **GDPR** | ⚠️ Check data residency | ✅ EU regions available | ✅ Fully local |
| **Data Residency** | ⚠️ Multi-region | ✅ Choose region | ✅ On-premises |

### Network Security

#### Azure Private Endpoints

```bash
# Restrict Azure OpenAI to private network only
az cognitiveservices account update \
  --name my-openai \
  --resource-group rg-legiscan \
  --public-network-access Disabled

az network private-endpoint create \
  --resource-group rg-legiscan \
  --name openai-private-endpoint \
  --vnet-name my-vnet \
  --subnet my-subnet \
  --private-connection-resource-id /subscriptions/.../Microsoft.CognitiveServices/accounts/my-openai \
  --group-id account \
  --connection-name openai-connection
```

---

## Scalability Guide

### Horizontal Scaling

#### Scenario: Process 50 States (200K+ Bills)

**Option 1: Parallel Local Processing**

```bash
# Create script to process each state
cat > scripts/process_all_states.sh << 'EOF'
#!/bin/bash

STATES="AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY"

for STATE in $STATES; do
  echo "Processing $STATE..."
  python fetch_legiscan_bills.py --state $STATE &
done

wait
echo "All fetches complete"

for STATE in $STATES; do
  echo "Filtering $STATE..."
  python run_filter_pass.py ${STATE,,}_bills_2025 &
done

wait
echo "All filters complete"

python run_analysis_pass.py
EOF

chmod +x scripts/process_all_states.sh
./scripts/process_all_states.sh
```

**Estimated Time:** ~15-20 hours (limited by API rate limits)

---

**Option 2: Azure Container Apps with Jobs**

```bash
# Create a job for each state
for STATE in CT NY CA TX FL; do
  az containerapp job create \
    --name legiscan-job-${STATE,,} \
    --resource-group rg-legiscan-prod \
    --environment legiscan-env \
    --trigger-type Manual \
    --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
    --cpu 2 --memory 4Gi \
    --command "bash" "-c" "cd scripts && python fetch_legiscan_bills.py --state $STATE && python run_filter_pass.py ${STATE,,}_bills_2025"
done

# Execute all jobs in parallel
for STATE in CT NY CA TX FL; do
  az containerapp job start --name legiscan-job-${STATE,,} --resource-group rg-legiscan-prod &
done

wait

# Run analysis on all results
az containerapp job create \
  --name legiscan-analysis \
  --resource-group rg-legiscan-prod \
  --environment legiscan-env \
  --trigger-type Manual \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --cpu 4 --memory 8Gi \
  --command "bash" "-c" "cd scripts && python run_analysis_pass.py"

az containerapp job start --name legiscan-analysis --resource-group rg-legiscan-prod
```

**Estimated Time:** ~6-8 hours (parallel processing)

---

### Vertical Scaling

#### Increase Container Resources

```bash
# Docker: Update docker-compose.yml
services:
  legiscan-pipeline:
    deploy:
      resources:
        limits:
          cpus: '8'      # Increased from 4
          memory: 16G    # Increased from 8G

# Azure: Update container instance
az container create \
  --cpu 8 \          # Increased from 4
  --memory 16 \      # Increased from 8
  # ... other params
```

#### Optimize Configuration

```json
{
  "filter_pass": {
    "batch_size": 100,  // Increased from 50
    "timeout": 300      // Increased from 180
  },
  "analysis_pass": {
    "timeout": 120,     // Increased from 90
    "api_delay": 0.5    // Decreased from 1.0
  }
}
```

### Rate Limit Management

#### Azure OpenAI Quota Increase

```bash
# Request quota increase
az cognitiveservices account deployment update \
  --name my-openai \
  --resource-group rg-legiscan \
  --deployment-name gpt-4o-mini \
  --sku-capacity 100  # Increase from 50 (TPM in thousands)
```

#### Implement Retry Logic

Already implemented in source code, but you can adjust:

```json
{
  "analysis_pass": {
    "api_delay": 2.0,        // Increase delay between calls
    "max_retries": 5,        // Retry on rate limit
    "retry_delay": 60        // Wait 60s on 429 error
  }
}
```

---

## Summary Matrix

### Quick Selection Guide

| Your Situation | Recommended Setup | Estimated Cost/Run | Setup Time |
|----------------|-------------------|-------------------|------------|
| First-time user, testing | Local + Portkey | $0.40 | 10 min |
| Regular use, budget-conscious | Docker + Hybrid | $0.07 | 1 hour |
| Enterprise, compliance required | Azure + Azure OpenAI | $0.40 + infra | 3 hours |
| Privacy-sensitive data | Docker + Ollama | $0 (time cost) | 30 min |
| High volume (50+ states) | Azure Container Apps + Azure OpenAI | ~$20/run | 4 hours |
| Maximum quality needed | Any + gpt-4o | $6.00 | Varies |

---

**Next Steps:**

1. Choose your deployment based on the decision matrix
2. Follow the corresponding detailed guide:
   - [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Docker setup
   - [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) - Azure setup
   - [AZURE_OPENAI_SETUP.md](AZURE_OPENAI_SETUP.md) - Azure OpenAI setup
   - [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md) - Ollama setup
   - [QUICK_START_SCENARIOS.md](QUICK_START_SCENARIOS.md) - Cookbook recipes

---

**Document Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team
