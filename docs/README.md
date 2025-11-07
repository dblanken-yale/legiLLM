# Documentation Index

Welcome to the LegiScan State Bill Analysis Pipeline documentation. This guide will help you find the right documentation for your needs.

## 🚀 Quick Start

**New to the project?** Start here:

1. [**Main README**](../README.md) - Project overview, features, and basic setup
2. [**QUICK_START_SCENARIOS.md**](QUICK_START_SCENARIOS.md) - Cookbook-style recipes for common setups
3. Choose your scenario from the decision tree below

## 📋 Decision Tree

### What do you want to do?

#### → I want to run the pipeline for the first time

**Best path:** Local setup with Portkey (10 minutes)

```
1. Read: QUICK_START_SCENARIOS.md → Scenario 1
2. Copy-paste commands
3. Done!
```

**Guides:**
- [Quick Start Scenarios - Scenario 1](QUICK_START_SCENARIOS.md#scenario-1-first-time-user-local--portkey)
- [Main README - Quick Start](../README.md#quick-start)

---

#### → I want to use Docker with Azure OpenAI and keep files local

**Best path:** Docker + Azure OpenAI (your specific use case!)

```
1. Read: QUICK_START_SCENARIOS.md → Scenario 2
2. Setup Azure OpenAI: AZURE_OPENAI_SETUP.md
3. Copy-paste commands from scenario
4. Done!
```

**Guides:**
- [Quick Start Scenarios - Scenario 2](QUICK_START_SCENARIOS.md#scenario-2-docker--azure-openai--local-files)
- [Azure OpenAI Setup](AZURE_OPENAI_SETUP.md)
- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md)

---

#### → I want to minimize costs ($0 API fees)

**Best path:** Docker + Ollama (local LLM)

```
1. Read: QUICK_START_SCENARIOS.md → Scenario 3
2. Setup Ollama: LOCAL_LLM_SETUP.md
3. Copy-paste commands
4. Done!
```

**Guides:**
- [Quick Start Scenarios - Scenario 3](QUICK_START_SCENARIOS.md#scenario-3-docker--ollama-zero-cost)
- [Local LLM Setup](LOCAL_LLM_SETUP.md)

---

#### → I want the best value (cost vs. quality)

**Best path:** Hybrid approach (Ollama filter + Azure analysis)

```
1. Read: QUICK_START_SCENARIOS.md → Scenario 4
2. Setup both Ollama and Azure OpenAI
3. Run filter with Ollama, analysis with Azure
4. Save 82% on costs!
```

**Guides:**
- [Quick Start Scenarios - Scenario 4](QUICK_START_SCENARIOS.md#scenario-4-hybrid-approach-best-value)
- [Deployment Guide - Hybrid Section](DEPLOYMENT_GUIDE.md#hybrid-approach)

---

#### → I want to deploy to production on Azure

**Best path:** Azure Container Instances or Container Apps

```
1. Read: AZURE_DEPLOYMENT.md
2. Follow step-by-step deployment
3. Setup Azure OpenAI: AZURE_OPENAI_SETUP.md
4. Deploy!
```

**Guides:**
- [Azure Deployment Guide](AZURE_DEPLOYMENT.md)
- [Azure OpenAI Setup](AZURE_OPENAI_SETUP.md)
- [Quick Start Scenarios - Scenario 5](QUICK_START_SCENARIOS.md#scenario-5-production-azure-deployment)

---

#### → I want to set up the UI dashboard

**Best path:** LegiUI local development

```
1. Read: legiUI/DEPLOYMENT.md
2. Install Node.js dependencies
3. Load data from analysis results
4. Start dev server
5. Done!
```

**Guides:**
- [LegiUI Deployment Guide](../legiUI/DEPLOYMENT.md)
- [LegiUI README](../legiUI/README.md)
- [Quick Start Scenarios - Scenario 7](QUICK_START_SCENARIOS.md#scenario-7-legiui-dashboard-setup)

---

#### → I want to understand all deployment options

**Best path:** Deployment comparison guide

```
1. Read: DEPLOYMENT_GUIDE.md
2. Review decision matrix
3. Compare costs, performance, security
4. Choose best option for your needs
```

**Guides:**
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Quick Start Scenarios](QUICK_START_SCENARIOS.md)

---

#### → I want to process multiple states

**Best path:** Parallel processing guide

```
1. Read: QUICK_START_SCENARIOS.md → Scenario 6
2. Setup your preferred environment
3. Run parallel processing
4. Done!
```

**Guides:**
- [Quick Start Scenarios - Scenario 6](QUICK_START_SCENARIOS.md#scenario-6-multiple-states-processing)
- [Deployment Guide - Scalability](DEPLOYMENT_GUIDE.md#scalability-guide)

---

## 📚 Complete Documentation

### Core Guides

| Document | Description | When to Read |
|----------|-------------|--------------|
| [**README.md**](../README.md) | Main project overview and quick start | First time setup |
| [**QUICK_START_SCENARIOS.md**](QUICK_START_SCENARIOS.md) | Cookbook-style recipes for common setups | When you know what you want to do |
| [**DEPLOYMENT_GUIDE.md**](DEPLOYMENT_GUIDE.md) | Complete comparison of all deployment options | Choosing deployment strategy |
| [**DOCKER_DEPLOYMENT.md**](DOCKER_DEPLOYMENT.md) | Detailed Docker setup for all scenarios | Using Docker |
| [**CLAUDE.md**](../CLAUDE.md) | Project instructions for Claude Code | Reference for AI assistance |

### Environment-Specific Guides

| Document | Description | When to Read |
|----------|-------------|--------------|
| [**AZURE_DEPLOYMENT.md**](AZURE_DEPLOYMENT.md) | Azure Container Instances/Apps deployment | Deploying to Azure |
| [**AZURE_OPENAI_SETUP.md**](AZURE_OPENAI_SETUP.md) | Azure OpenAI resource setup and configuration | Using Azure OpenAI |
| [**LOCAL_LLM_SETUP.md**](LOCAL_LLM_SETUP.md) | Ollama setup for local LLM processing | Using local LLMs |
| [**LOCAL_VS_AZURE.md**](LOCAL_VS_AZURE.md) | Comparison of local vs Azure deployments | Deciding between local and cloud |

### Technical Documentation

| Document | Description | When to Read |
|----------|-------------|--------------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | System design and architecture | Understanding internals |
| [**CONFIGURATION.md**](CONFIGURATION.md) | Configuration options and examples | Customizing behavior |
| [**AI_PROCESSOR.md**](AI_PROCESSOR.md) | AI processing details and prompts | Understanding AI analysis |
| [**PLUGINS.md**](PLUGINS.md) | Data source plugin system | Adding custom data sources |

### UI Documentation

| Document | Description | When to Read |
|----------|-------------|--------------|
| [**legiUI/README.md**](../legiUI/README.md) | LegiUI dashboard overview | Setting up the UI |
| [**legiUI/DEPLOYMENT.md**](../legiUI/DEPLOYMENT.md) | LegiUI deployment options | Deploying the dashboard |

### Additional Resources

| Document | Description | When to Read |
|----------|-------------|--------------|
| [**IMPLEMENTATION_STATUS.md**](IMPLEMENTATION_STATUS.md) | Feature implementation status | Checking what's implemented |
| [**QUICK_START.md**](QUICK_START.md) | Quick start guide | Alternative quick start |
| [**SECURITY_AUDIT_COMMIT.md**](SECURITY_AUDIT_COMMIT.md) | Security audit findings | Security review |

---

## 🎯 By Use Case

### For Developers

**Getting Started:**
1. [Main README](../README.md) - Overview
2. [Quick Start Scenarios - Scenario 1](QUICK_START_SCENARIOS.md#scenario-1-first-time-user-local--portkey) - First setup
3. [Architecture Guide](ARCHITECTURE.md) - Understand the system

**Advanced Topics:**
- [Configuration Guide](CONFIGURATION.md) - Customize behavior
- [AI Processor Guide](AI_PROCESSOR.md) - Understand AI processing
- [Plugins Guide](PLUGINS.md) - Extend functionality

---

### For DevOps / Infrastructure

**Cloud Deployment:**
1. [Deployment Guide](DEPLOYMENT_GUIDE.md) - Compare options
2. [Azure Deployment](AZURE_DEPLOYMENT.md) - Azure specifics
3. [Docker Deployment](DOCKER_DEPLOYMENT.md) - Container details

**Cost Optimization:**
- [Local LLM Setup](LOCAL_LLM_SETUP.md) - Zero API costs
- [Deployment Guide - Cost Analysis](DEPLOYMENT_GUIDE.md#cost-analysis)
- [Quick Start Scenarios - Scenario 4](QUICK_START_SCENARIOS.md#scenario-4-hybrid-approach-best-value) - Hybrid approach

---

### For Data Analysts

**Dashboard Setup:**
1. [legiUI README](../legiUI/README.md) - Dashboard overview
2. [legiUI Deployment](../legiUI/DEPLOYMENT.md) - Deploy dashboard
3. [Quick Start Scenarios - Scenario 7](QUICK_START_SCENARIOS.md#scenario-7-legiui-dashboard-setup) - Step-by-step

**Running Analysis:**
- [Main README - Quick Start](../README.md#quick-start) - Run pipeline
- [Quick Start Scenarios](QUICK_START_SCENARIOS.md) - Common workflows
- [Configuration Guide](CONFIGURATION.md) - Adjust analysis parameters

---

### For Compliance / Security

**Enterprise Deployment:**
1. [Azure OpenAI Setup](AZURE_OPENAI_SETUP.md) - Enterprise LLM
2. [Azure Deployment](AZURE_DEPLOYMENT.md) - Secure infrastructure
3. [Deployment Guide - Security](DEPLOYMENT_GUIDE.md#security-considerations) - Security review

**Data Privacy:**
- [Local LLM Setup](LOCAL_LLM_SETUP.md) - Fully local processing
- [Deployment Guide - Privacy](DEPLOYMENT_GUIDE.md#security-considerations) - Privacy options
- [Docker Deployment - Ollama](DOCKER_DEPLOYMENT.md#scenario-3-docker--ollama-local-llm) - Offline capable

---

## 🔧 By Technology

### Docker

**Primary Guide:** [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

**Related:**
- [Quick Start Scenarios - Scenario 2](QUICK_START_SCENARIOS.md#scenario-2-docker--azure-openai--local-files) - Docker + Azure OpenAI
- [Quick Start Scenarios - Scenario 3](QUICK_START_SCENARIOS.md#scenario-3-docker--ollama-zero-cost) - Docker + Ollama
- [Deployment Guide - Docker Section](DEPLOYMENT_GUIDE.md#docker-local)

---

### Azure

**Primary Guides:**
- [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) - Azure infrastructure
- [AZURE_OPENAI_SETUP.md](AZURE_OPENAI_SETUP.md) - Azure OpenAI

**Related:**
- [Quick Start Scenarios - Scenario 5](QUICK_START_SCENARIOS.md#scenario-5-production-azure-deployment)
- [Deployment Guide - Azure Sections](DEPLOYMENT_GUIDE.md#azure-container-instances)

---

### Local LLMs (Ollama)

**Primary Guide:** [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)

**Related:**
- [Quick Start Scenarios - Scenario 3](QUICK_START_SCENARIOS.md#scenario-3-docker--ollama-zero-cost)
- [Quick Start Scenarios - Scenario 4](QUICK_START_SCENARIOS.md#scenario-4-hybrid-approach-best-value)
- [Deployment Guide - Ollama Section](DEPLOYMENT_GUIDE.md#ollama-local-llm)

---

### React / LegiUI

**Primary Guides:**
- [legiUI/README.md](../legiUI/README.md) - Overview
- [legiUI/DEPLOYMENT.md](../legiUI/DEPLOYMENT.md) - Deployment

**Related:**
- [Quick Start Scenarios - Scenario 7](QUICK_START_SCENARIOS.md#scenario-7-legiui-dashboard-setup)
- [Main README - LegiUI Section](../README.md#legiui---visualization-dashboard)

---

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| **Can't connect to API** | Check API keys in .env | [Configuration Guide](CONFIGURATION.md) |
| **Docker container won't start** | Check Docker logs | [Docker Deployment - Troubleshooting](DOCKER_DEPLOYMENT.md#troubleshooting) |
| **Data not loading in UI** | Run `npm run load-data` | [legiUI Deployment - Troubleshooting](../legiUI/DEPLOYMENT.md#troubleshooting) |
| **High API costs** | Use Ollama or hybrid approach | [Local LLM Setup](LOCAL_LLM_SETUP.md) |
| **Slow performance** | Adjust batch size, use caching | [Configuration Guide](CONFIGURATION.md) |
| **Azure deployment fails** | Check Azure quotas and permissions | [Azure Deployment - Troubleshooting](AZURE_DEPLOYMENT.md) |

### Getting Help

1. Check relevant documentation above
2. Review [Quick Start Scenarios](QUICK_START_SCENARIOS.md) for working examples
3. Check GitHub Issues
4. Review [Architecture Guide](ARCHITECTURE.md) for system understanding

---

## 📖 Reading Order

### For First-Time Users

```
1. Main README (10 min)
   ↓
2. Quick Start Scenarios - Pick your scenario (15 min)
   ↓
3. Follow scenario step-by-step (30 min - 4 hours)
   ↓
4. LegiUI setup (10 min)
   ↓
5. Done! Explore advanced features as needed
```

### For Production Deployment

```
1. Deployment Guide (30 min)
   ↓
2. Choose: Azure or Docker deployment
   ↓
3. If Azure:
   - Azure Deployment Guide (2 hours)
   - Azure OpenAI Setup (1 hour)
   ↓
4. If Docker:
   - Docker Deployment Guide (1 hour)
   ↓
5. Security review (30 min)
   ↓
6. Deploy and test
```

### For Understanding the System

```
1. Main README (10 min)
   ↓
2. Architecture Guide (30 min)
   ↓
3. Configuration Guide (20 min)
   ↓
4. AI Processor Guide (20 min)
   ↓
5. Experiment with Quick Start Scenarios
```

---

## 🔍 Search by Topic

### API Keys
- [Configuration Guide](CONFIGURATION.md)
- [Azure OpenAI Setup - API Credentials](AZURE_OPENAI_SETUP.md#step-4-get-api-credentials)
- [Quick Start Scenarios - All](QUICK_START_SCENARIOS.md)

### Batch Processing
- [Configuration Guide - Batch Settings](CONFIGURATION.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Deployment Guide - Performance](DEPLOYMENT_GUIDE.md#performance-benchmarks)

### Caching
- [Configuration Guide - LegiScan Caching](CONFIGURATION.md)
- [Architecture Guide - Data Flow](ARCHITECTURE.md)

### Cost Optimization
- [Deployment Guide - Cost Analysis](DEPLOYMENT_GUIDE.md#cost-analysis)
- [Local LLM Setup](LOCAL_LLM_SETUP.md)
- [Quick Start Scenarios - Scenario 4](QUICK_START_SCENARIOS.md#scenario-4-hybrid-approach-best-value)

### Data Sources
- [Plugins Guide](PLUGINS.md)
- [Configuration Guide](CONFIGURATION.md)

### LegiScan API
- [Main README - API Keys](../README.md#api-keys)
- [Architecture Guide](ARCHITECTURE.md)

### Parallel Processing
- [Quick Start Scenarios - Scenario 6](QUICK_START_SCENARIOS.md#scenario-6-multiple-states-processing)
- [Deployment Guide - Scalability](DEPLOYMENT_GUIDE.md#scalability-guide)

### Prompts
- [AI Processor Guide](AI_PROCESSOR.md)
- [Main README - Customizing Prompts](../README.md#customizing-prompts)

### Security
- [Deployment Guide - Security](DEPLOYMENT_GUIDE.md#security-considerations)
- [Azure OpenAI Setup - Security Best Practices](AZURE_OPENAI_SETUP.md#security-best-practices)

### Testing
- [Quick Start Scenarios - Scenario 8](QUICK_START_SCENARIOS.md#scenario-8-testing-with-5-bills)
- [Main README - Test Mode](../README.md#test-mode)

---

## 📊 Documentation Status

| Category | Coverage | Last Updated |
|----------|----------|--------------|
| Getting Started | ✅ Complete | 2025-02-07 |
| Deployment | ✅ Complete | 2025-02-07 |
| Configuration | ✅ Complete | 2025-02-07 |
| UI/Dashboard | ✅ Complete | 2025-02-07 |
| Architecture | ✅ Complete | 2024-12-01 |
| Troubleshooting | ✅ Complete | 2025-02-07 |

---

## 🚦 Quick Links

### Most Common Paths

| I want to... | Start here |
|-------------|-----------|
| **Try it out quickly** | [Quick Start Scenarios - Scenario 1](QUICK_START_SCENARIOS.md#scenario-1-first-time-user-local--portkey) |
| **Use Docker + Azure OpenAI** | [Quick Start Scenarios - Scenario 2](QUICK_START_SCENARIOS.md#scenario-2-docker--azure-openai--local-files) |
| **Save money** | [Quick Start Scenarios - Scenario 4](QUICK_START_SCENARIOS.md#scenario-4-hybrid-approach-best-value) |
| **Deploy to production** | [Azure Deployment Guide](AZURE_DEPLOYMENT.md) |
| **Set up the dashboard** | [legiUI Deployment](../legiUI/DEPLOYMENT.md) |
| **Understand the system** | [Architecture Guide](ARCHITECTURE.md) |
| **Compare all options** | [Deployment Guide](DEPLOYMENT_GUIDE.md) |

---

## 💡 Tips for Reading

1. **Start with scenarios, not guides** - The [Quick Start Scenarios](QUICK_START_SCENARIOS.md) give you working examples you can copy-paste
2. **Use the decision tree** - Don't read everything, find your path above
3. **Bookmark this page** - Use it as your navigation hub
4. **Follow the "Related" links** - Each guide links to relevant docs
5. **Check troubleshooting sections** - Most guides have troubleshooting at the end

---

## 📝 Contributing to Docs

Found an error or want to improve documentation?

1. Check if the issue is already documented
2. Identify which document needs updating (use this index)
3. Make changes following existing format
4. Update "Last Updated" date in document footer
5. Update this index if adding new documents

---

**Documentation Version:** 1.0
**Last Updated:** 2025-02-07
**Maintained By:** Development Team

---

**Need help navigating?** Start with the [Decision Tree](#-decision-tree) above!
