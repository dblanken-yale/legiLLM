# Azure OpenAI Setup Guide

This guide provides step-by-step instructions for switching from Portkey to Azure OpenAI as your LLM provider for the LegiScan Bill Analysis Pipeline.

## Overview

Azure OpenAI Service provides enterprise-grade access to OpenAI models with:
- **Enhanced Security**: Data stays within your Azure tenant
- **Compliance**: Meets enterprise compliance requirements (HIPAA, SOC 2, etc.)
- **Cost Control**: Predictable pricing and spending limits
- **Integration**: Seamless integration with Azure services
- **No Proxies**: Direct access without third-party services like Portkey

## Prerequisites

- Azure subscription with access to create resources
- Permissions to create Azure OpenAI resources (requires approval in some regions)
- Python 3.8+ installed locally
- Existing LegiScan Bill Analysis Pipeline setup

## Step 1: Request Azure OpenAI Access

Azure OpenAI requires explicit approval before you can create resources.

### 1.1 Apply for Access

1. Visit the [Azure OpenAI Access Request Form](https://aka.ms/oai/access)
2. Fill out the required information:
   - Business use case description
   - Expected usage volume
   - Compliance requirements
3. Wait for approval (typically 1-3 business days)

### 1.2 Verify Access

Once approved, verify you can access Azure OpenAI:

```bash
az login
az account set --subscription <your-subscription-id>

# Check if Azure OpenAI is available
az provider show --namespace Microsoft.CognitiveServices --query "registrationState"
```

Expected output: `"Registered"`

## Step 2: Create Azure OpenAI Resource

### 2.1 Using Azure Portal (Recommended for First-Time Setup)

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"Azure OpenAI"**
4. Click **"Create"**
5. Fill in the details:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing (e.g., `rg-legiscan-prod`)
   - **Region**: Choose a region that supports OpenAI (e.g., `East US`, `West Europe`, `Japan East`)
   - **Name**: Unique name (e.g., `legiscan-openai-prod`)
   - **Pricing Tier**: Standard S0 (pay-as-you-go)
6. Click **"Review + create"** then **"Create"**
7. Wait for deployment to complete (~2-3 minutes)

### 2.2 Using Azure CLI

```bash
# Create resource group (if not exists)
az group create \
  --name rg-legiscan-prod \
  --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name legiscan-openai-prod \
  --resource-group rg-legiscan-prod \
  --location eastus \
  --kind OpenAI \
  --sku S0 \
  --custom-domain legiscan-openai-prod
```

**Available Regions** (as of 2025):
- East US
- East US 2
- South Central US
- West Europe
- France Central
- UK South
- Japan East
- Sweden Central

Check current availability: [Azure OpenAI Service regions](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability)

## Step 3: Deploy a Model

Azure OpenAI requires you to explicitly deploy models before use.

### 3.1 Deploy via Azure Portal

1. Navigate to your Azure OpenAI resource
2. Click **"Go to Azure OpenAI Studio"**
3. In the left sidebar, click **"Deployments"**
4. Click **"+ Create new deployment"**
5. Configure deployment:
   - **Model**: Select `gpt-4o-mini` (recommended for cost-effectiveness)
   - **Deployment name**: `gpt-4o-mini` (use same name as model for simplicity)
   - **Model version**: Latest stable version
   - **Deployment type**: Standard
   - **Tokens per minute rate limit**: 50K (adjust based on needs)
6. Click **"Create"**
7. Wait for deployment (~1-2 minutes)

### 3.2 Deploy via Azure CLI

```bash
# List available models
az cognitiveservices account deployment list \
  --name legiscan-openai-prod \
  --resource-group rg-legiscan-prod

# Create deployment
az cognitiveservices account deployment create \
  --name legiscan-openai-prod \
  --resource-group rg-legiscan-prod \
  --deployment-name gpt-4o-mini \
  --model-name gpt-4o-mini \
  --model-version "2024-07-18" \
  --model-format OpenAI \
  --sku-capacity 50 \
  --sku-name Standard
```

**Recommended Models:**
- **gpt-4o-mini**: Best cost-performance ratio, suitable for most analysis tasks
- **gpt-4o**: Higher capability, use for complex analysis requiring better reasoning
- **gpt-35-turbo**: Lowest cost, suitable for simple filtering tasks

**Rate Limits:**
- Start with 50K tokens per minute (TPM)
- Monitor usage and adjust as needed
- Request quota increases if you hit limits

## Step 4: Get API Credentials

### 4.1 Get Endpoint URL

**Via Azure Portal:**
1. Navigate to your Azure OpenAI resource
2. Click **"Keys and Endpoint"** in the left sidebar
3. Copy the **"Endpoint"** value (e.g., `https://legiscan-openai-prod.openai.azure.com/`)

**Via Azure CLI:**
```bash
az cognitiveservices account show \
  --name legiscan-openai-prod \
  --resource-group rg-legiscan-prod \
  --query "properties.endpoint" \
  --output tsv
```

### 4.2 Get API Key

**Via Azure Portal:**
1. In **"Keys and Endpoint"**, copy **"KEY 1"**
2. Store securely (do not commit to git)

**Via Azure CLI:**
```bash
az cognitiveservices account keys list \
  --name legiscan-openai-prod \
  --resource-group rg-legiscan-prod \
  --query "key1" \
  --output tsv
```

### 4.3 Get Deployment Name

Use the deployment name you created in Step 3 (e.g., `gpt-4o-mini`)

## Step 5: Configure Your Application

### 5.1 Update Environment Variables

Edit your `.env` file:

```bash
# Remove or comment out Portkey
# PORTKEY_API_KEY=your_portkey_key

# Add Azure OpenAI credentials
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://legiscan-openai-prod.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Keep LegiScan API key
LEGISCAN_API_KEY=your_legiscan_key
```

**Security Note:** Never commit `.env` file to git. It's already in `.gitignore`.

### 5.2 Create or Update config.json

Create `config.json` in your project root (or copy from example):

```bash
cp config_examples/config_azure_example.json config.json
```

Edit `config.json`:

```json
{
  "llm": {
    "provider": "azure",
    "deployment_name": "gpt-4o-mini",
    "endpoint": "https://legiscan-openai-prod.openai.azure.com/",
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
```

**Configuration Notes:**
- `api_key: null` means the app will use the `AZURE_OPENAI_API_KEY` environment variable
- You can set `api_key` directly in config, but environment variables are more secure
- `api_version` should match Azure's current stable API version
- `deployment_name` must match exactly what you created in Step 3

### 5.3 Install Required Dependencies

Ensure you have the Azure OpenAI SDK:

```bash
pip install openai>=1.0.0
```

Verify installation:

```bash
python -c "import openai; print(openai.__version__)"
```

Expected output: `1.x.x` (version 1.0.0 or higher)

## Step 6: Test the Configuration

### 6.1 Quick Test Script

Create a test script to verify connectivity:

```bash
cd scripts
python -c "
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version='2024-02-15-preview',
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

response = client.chat.completions.create(
    model=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
    messages=[{'role': 'user', 'content': 'Hello, Azure OpenAI!'}],
    max_tokens=50
)

print('✅ Azure OpenAI connection successful!')
print(f'Response: {response.choices[0].message.content}')
"
```

Expected output:
```
✅ Azure OpenAI connection successful!
Response: Hello! How can I assist you today?
```

### 6.2 Test with Pipeline (Test Mode)

Run the analysis pipeline in test mode:

```bash
export TEST_MODE=true
export TEST_COUNT=3

cd scripts
python run_filter_pass.py
```

Expected behavior:
- Script connects to Azure OpenAI
- Processes 3 bills
- Creates filter results in `data/filtered/`
- No errors about API keys or endpoints

### 6.3 Test Analysis Pass

```bash
export TEST_MODE=true
export TEST_COUNT=3

cd scripts
python run_analysis_pass.py
```

Expected behavior:
- Fetches full bill text from LegiScan
- Sends to Azure OpenAI for analysis
- Creates analysis results in `data/analyzed/`
- Response times similar to Portkey (may vary by region)

## Step 7: Monitor Usage and Costs

### 7.1 Check Usage in Azure Portal

1. Navigate to your Azure OpenAI resource
2. Click **"Metrics"** in the left sidebar
3. Add metrics:
   - **Total Tokens**: Track total token usage
   - **Generated Tokens**: Track output tokens (more expensive)
   - **Processed Prompt Tokens**: Track input tokens
   - **Total Calls**: Number of API requests
4. Set time range to **"Last 24 hours"**
5. Monitor for unexpected spikes

### 7.2 Set Up Cost Alerts

```bash
# Create cost alert for Azure OpenAI resource
az consumption budget create \
  --resource-group rg-legiscan-prod \
  --budget-name openai-monthly-budget \
  --amount 100 \
  --time-grain Monthly \
  --start-date 2025-02-01 \
  --end-date 2026-01-31 \
  --category Cost \
  --notifications amount=80 contactEmails=your-email@domain.com
```

### 7.3 Estimate Costs

**Pricing (as of January 2025):**

**gpt-4o-mini:**
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**gpt-4o:**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

**Example Cost Calculation:**

Analyzing 4,000 bills with gpt-4o-mini:
- Filter pass (50 bills/batch, 80 batches):
  - Input: ~500 tokens/bill × 4,000 = 2M tokens × $0.150 = $0.30
  - Output: ~100 tokens/batch × 80 = 8K tokens × $0.600 = $0.005
- Analysis pass (68 relevant bills):
  - Input: ~3,000 tokens/bill × 68 = 204K tokens × $0.150 = $0.03
  - Output: ~1,000 tokens/bill × 68 = 68K tokens × $0.600 = $0.04

**Total: ~$0.38 per full pipeline run**

This is significantly cheaper than gpt-4o (~$5-10 per run).

## Troubleshooting

### Issue: "Resource not found" error

**Cause:** Incorrect endpoint URL or deployment name

**Solution:**
1. Verify endpoint URL matches exactly (including trailing slash):
   ```bash
   echo $AZURE_OPENAI_ENDPOINT
   # Should be: https://your-resource.openai.azure.com/
   ```
2. Verify deployment name matches exactly:
   ```bash
   az cognitiveservices account deployment list \
     --name legiscan-openai-prod \
     --resource-group rg-legiscan-prod \
     --query "[].name"
   ```
3. Update `config.json` or environment variables to match

### Issue: "401 Unauthorized" error

**Cause:** Invalid or expired API key

**Solution:**
1. Regenerate API key:
   ```bash
   az cognitiveservices account keys regenerate \
     --name legiscan-openai-prod \
     --resource-group rg-legiscan-prod \
     --key-name key1
   ```
2. Update `.env` file with new key:
   ```bash
   AZURE_OPENAI_API_KEY=your_new_key_here
   ```
3. Restart your application

### Issue: "429 Rate Limit Exceeded" error

**Cause:** Exceeded tokens per minute (TPM) quota

**Solution:**
1. Check current quota:
   ```bash
   az cognitiveservices account deployment show \
     --name legiscan-openai-prod \
     --resource-group rg-legiscan-prod \
     --deployment-name gpt-4o-mini \
     --query "properties.rateLimits"
   ```
2. **Option A**: Reduce batch size in `config.json`:
   ```json
   {
     "filter_pass": {
       "batch_size": 25  // Reduced from 50
     }
   }
   ```
3. **Option B**: Increase rate limit quota:
   - Navigate to Azure OpenAI Studio
   - Go to **Quotas**
   - Request quota increase
   - Wait for approval (1-2 business days)

### Issue: "Model not found" error

**Cause:** Deployment name doesn't match or model not deployed

**Solution:**
1. List all deployments:
   ```bash
   az cognitiveservices account deployment list \
     --name legiscan-openai-prod \
     --resource-group rg-legiscan-prod \
     --output table
   ```
2. Verify deployment name in config matches deployment name in Azure
3. If no deployments exist, create one (see Step 3)

### Issue: Slow response times

**Cause:** Region latency or model performance

**Solution:**
1. Check region latency:
   - Use Azure regions closer to your location
   - Consider moving resource to different region
2. Switch to faster model:
   - `gpt-4o-mini` is fastest
   - `gpt-35-turbo` is even faster but less capable
3. Enable parallel processing:
   ```json
   {
     "filter_pass": {
       "batch_size": 50  // Process more bills per request
     }
   }
   ```

### Issue: Timeout errors

**Cause:** Requests taking longer than timeout setting

**Solution:**
1. Increase timeout in `config.json`:
   ```json
   {
     "filter_pass": {
       "timeout": 300  // Increased from 180 seconds
     },
     "analysis_pass": {
       "timeout": 120  // Increased from 90 seconds
     }
   }
   ```
2. Reduce batch size to process fewer bills per request
3. Check Azure OpenAI service status: [Azure Status](https://status.azure.com)

### Issue: "API version not supported" error

**Cause:** Using outdated or incorrect API version

**Solution:**
1. Update to current stable version in `config.json`:
   ```json
   {
     "llm": {
       "api_version": "2024-02-15-preview"
     }
   }
   ```
2. Check latest API version: [Azure OpenAI API versions](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)

## Security Best Practices

### 1. Secure API Keys

**DO:**
- ✅ Store API keys in `.env` file (gitignored)
- ✅ Use Azure Key Vault for production
- ✅ Rotate keys regularly (every 90 days)
- ✅ Use different keys for dev/staging/prod

**DON'T:**
- ❌ Commit API keys to git
- ❌ Share keys via email or chat
- ❌ Hard-code keys in source files
- ❌ Use production keys in development

### 2. Use Azure Key Vault (Production)

For production deployments, use Azure Key Vault:

```bash
# Create Key Vault
az keyvault create \
  --name kv-legiscan-prod \
  --resource-group rg-legiscan-prod \
  --location eastus

# Store API key
az keyvault secret set \
  --vault-name kv-legiscan-prod \
  --name AZURE-OPENAI-API-KEY \
  --value "your-api-key"

# Store endpoint
az keyvault secret set \
  --vault-name kv-legiscan-prod \
  --name AZURE-OPENAI-ENDPOINT \
  --value "https://legiscan-openai-prod.openai.azure.com/"

# Grant access to managed identity
az keyvault set-policy \
  --name kv-legiscan-prod \
  --object-id <managed-identity-id> \
  --secret-permissions get list
```

Update your application to fetch from Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://kv-legiscan-prod.vault.azure.net/", credential=credential)

api_key = client.get_secret("AZURE-OPENAI-API-KEY").value
endpoint = client.get_secret("AZURE-OPENAI-ENDPOINT").value
```

### 3. Network Security

**Enable Private Endpoints (Optional):**
- Restricts access to Azure OpenAI from within your virtual network
- Prevents public internet access
- Recommended for highly sensitive workloads

```bash
# Disable public network access
az cognitiveservices account update \
  --name legiscan-openai-prod \
  --resource-group rg-legiscan-prod \
  --public-network-access Disabled

# Create private endpoint (requires VNet)
az network private-endpoint create \
  --resource-group rg-legiscan-prod \
  --name openai-private-endpoint \
  --vnet-name your-vnet \
  --subnet your-subnet \
  --private-connection-resource-id /subscriptions/.../resourceGroups/rg-legiscan-prod/providers/Microsoft.CognitiveServices/accounts/legiscan-openai-prod \
  --group-id account \
  --connection-name openai-connection
```

### 4. Audit Logging

Enable diagnostic logging to track API usage:

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group rg-legiscan-prod \
  --workspace-name legiscan-logs

# Enable diagnostic settings
az monitor diagnostic-settings create \
  --name openai-diagnostics \
  --resource /subscriptions/.../resourceGroups/rg-legiscan-prod/providers/Microsoft.CognitiveServices/accounts/legiscan-openai-prod \
  --workspace legiscan-logs \
  --logs '[{"category": "Audit", "enabled": true}]' \
  --metrics '[{"category": "AllMetrics", "enabled": true}]'
```

## Comparison: Portkey vs Azure OpenAI

| Feature | Portkey | Azure OpenAI |
|---------|---------|--------------|
| **Setup Complexity** | Simple (just API key) | Moderate (Azure resource creation) |
| **Cost** | OpenAI pricing + Portkey fee | OpenAI pricing only |
| **Data Residency** | Multi-region (Portkey controlled) | Your Azure region |
| **Compliance** | Portkey SOC 2 | Azure compliance (HIPAA, SOC 2, etc.) |
| **Enterprise Features** | Limited | Full Azure integration |
| **Rate Limits** | OpenAI standard | Configurable quotas |
| **Monitoring** | Portkey dashboard | Azure Monitor + App Insights |
| **API Compatibility** | OpenAI standard | Azure-specific endpoints |

**When to Use Azure OpenAI:**
- ✅ Enterprise compliance requirements (HIPAA, SOC 2, FedRAMP)
- ✅ Need data residency in specific regions
- ✅ Want integration with Azure services
- ✅ Require granular cost control and monitoring
- ✅ Need higher rate limits

**When to Use Portkey:**
- ✅ Simple setup with minimal configuration
- ✅ Multi-provider support (OpenAI, Anthropic, etc.)
- ✅ Don't need enterprise compliance
- ✅ Prefer unified API across multiple LLM providers

## Migration Checklist

Use this checklist to ensure smooth migration from Portkey to Azure OpenAI:

### Pre-Migration
- [ ] Request Azure OpenAI access (Step 1)
- [ ] Create Azure OpenAI resource (Step 2)
- [ ] Deploy model (gpt-4o-mini recommended) (Step 3)
- [ ] Collect API credentials (Step 4)
- [ ] Backup current config and .env files

### Configuration
- [ ] Update `.env` with Azure credentials (Step 5.1)
- [ ] Create or update `config.json` (Step 5.2)
- [ ] Install required dependencies (Step 5.3)
- [ ] Verify configuration files are gitignored

### Testing
- [ ] Run connectivity test (Step 6.1)
- [ ] Test filter pass with TEST_MODE=true (Step 6.2)
- [ ] Test analysis pass with TEST_MODE=true (Step 6.3)
- [ ] Compare results with previous Portkey runs
- [ ] Verify performance (response times, accuracy)

### Monitoring
- [ ] Set up usage metrics dashboard (Step 7.1)
- [ ] Create cost alerts (Step 7.2)
- [ ] Review first week of usage
- [ ] Adjust rate limits if needed

### Production
- [ ] Run full pipeline on real data
- [ ] Monitor for errors or timeouts
- [ ] Document any configuration changes
- [ ] Update team documentation
- [ ] Archive Portkey API keys (don't delete immediately)

### Post-Migration (1 week later)
- [ ] Review cost reports
- [ ] Compare costs: Azure OpenAI vs Portkey
- [ ] Optimize batch sizes and timeouts
- [ ] Remove Portkey API keys from .env
- [ ] Update CLAUDE.md with Azure-specific notes

## Additional Resources

### Official Documentation
- [Azure OpenAI Service Overview](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview)
- [Quickstart: Get started using Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart)
- [Azure OpenAI API Reference](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)
- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)

### Azure CLI Reference
- [az cognitiveservices](https://learn.microsoft.com/en-us/cli/azure/cognitiveservices)
- [az keyvault](https://learn.microsoft.com/en-us/cli/azure/keyvault)

### Python SDK
- [OpenAI Python Library](https://github.com/openai/openai-python)
- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)

### Support
- [Azure OpenAI Support](https://azure.microsoft.com/en-us/support/create-ticket/)
- [Azure Status Dashboard](https://status.azure.com)

## Next Steps

After successfully configuring Azure OpenAI:

1. **Optimize Performance**: Experiment with different models and batch sizes to find optimal cost-performance ratio
2. **Scale Up**: Remove `TEST_MODE` and run on full dataset
3. **Automate**: Set up Azure Container Apps for scheduled pipeline runs (see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md))
4. **Monitor**: Track usage and costs weekly, adjust quotas as needed
5. **Enhance**: Consider implementing caching layer for repeated queries

## Support and Feedback

For questions or issues:
- **Project Documentation**: See `docs/` directory
- **Azure OpenAI Issues**: Create Azure support ticket
- **Configuration Help**: Check `config_examples/config_azure_example.json`

---

**Document Version**: 1.0
**Last Updated**: 2025-02-07
**Maintained By**: Development Team
