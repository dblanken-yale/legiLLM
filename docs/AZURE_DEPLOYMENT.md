# Azure Deployment Guide

## Overview

This guide documents the Azure deployment architecture for the LegiScan Bill Analysis Pipeline. The implementation uses a **storage abstraction layer** that allows the application to run identically in both local and Azure environments while enabling shared team access through Azure Database for PostgreSQL.

## Architecture Principles

### 1. Local-First Development
- Default behavior remains file-based for ease of development
- Developers can work entirely locally without Azure credentials
- Same commands work in both local and Azure environments

### 2. Configuration-Driven Backend Selection
- Environment variable `STORAGE_BACKEND` determines storage provider
- Options: `local` (files), `azure_blob` (Azure Blob Storage), `database` (PostgreSQL)
- No code changes required to switch backends

### 3. Gradual Migration Path
- Dual-write mode supports both files and database simultaneously
- Enables validation and testing during transition
- Historical data can be migrated incrementally

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Python Scripts (UNCHANGED)                             │
│  ├── fetch_legiscan_bills.py                           │
│  ├── run_filter_pass.py                                │
│  ├── run_analysis_pass.py                              │
│  └── run_direct_analysis.py                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  Storage Abstraction Layer                              │
│  ├── StorageProvider (abstract base class)              │
│  ├── LocalFileStorage (current file behavior)           │
│  ├── AzureBlobStorage (Azure Blob Storage)              │
│  └── DatabaseStorage (PostgreSQL/CosmosDB)              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
      ┌──────────┴──────────┐
      │                     │
┌─────▼─────┐      ┌────────▼────────┐
│   Local   │      │     Azure       │
│   Files   │      │  PostgreSQL     │
│  data/    │      │  + Blob Storage │
└───────────┘      │  + Key Vault    │
                   └─────────────────┘
```

## Azure Resources

### Resource Group: `rg-legiscan-prod`

#### 1. Azure Database for PostgreSQL (Flexible Server)
- **SKU**: Burstable B1ms (1 vCore, 2GB RAM)
- **Database**: `legiscan_data`
- **Purpose**: Primary data storage for bills, filter results, analysis results, and cache
- **Estimated Cost**: ~$15-30/month

#### 2. Azure Container Apps
- **Name**: `legiscan-pipeline`
- **Purpose**: Run Python scripts as scheduled jobs or on-demand
- **Image**: Custom Docker container with Python 3.x + dependencies
- **Scaling**: Manual (0-1 instances, scales to 0 when idle)
- **Environment Variables**: Loaded from Key Vault
- **Estimated Cost**: ~$5-10/month (minimal compute time)

#### 3. Azure Key Vault
- **Name**: `kv-legiscan-prod`
- **Purpose**: Secure storage for API keys and connection strings
- **Secrets**:
  - `PORTKEY-API-KEY`
  - `LEGISCAN-API-KEY`
  - `DATABASE-CONNECTION-STRING`
- **Estimated Cost**: ~$1/month

#### 4. Azure Blob Storage (Optional)
- **Storage Account**: `stlegiscanprod`
- **Container**: `legiscan-data`
- **Purpose**: Optional file-based storage or backups
- **Tier**: Hot (Standard LRS)
- **Estimated Cost**: ~$0.50-2/month for ~10-50GB

#### 5. Azure Static Web Apps
- **Name**: `legiscan-ui`
- **Purpose**: Host React dashboard (legiUI)
- **Tier**: Free
- **API Backend**: Azure Functions (Node.js) connecting to PostgreSQL
- **Estimated Cost**: $0 (Free tier)

#### 6. Azure Application Insights
- **Purpose**: Monitoring, logging, and performance tracking
- **Integration**: Container Apps + Static Web Apps
- **Estimated Cost**: ~$2-5/month (low volume)

### Total Estimated Monthly Cost: **$25-50/month**

## Database Schema

### Tables

#### 1. `bills` - Raw bill data from LegiScan
```sql
CREATE TABLE bills (
    bill_id BIGINT PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL,
    state VARCHAR(2) NOT NULL,
    session VARCHAR(100),
    title TEXT,
    description TEXT,
    status INT,
    status_desc VARCHAR(100),
    year INT,
    change_hash VARCHAR(64),
    last_action TEXT,
    last_action_date DATE,
    url TEXT,
    state_url TEXT,
    raw_data JSONB,  -- Full LegiScan API response
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bill_number ON bills(bill_number);
CREATE INDEX idx_state_year ON bills(state, year);
CREATE INDEX idx_session ON bills(session);
```

#### 2. `filter_results` - Filter pass results
```sql
CREATE TABLE filter_results (
    id SERIAL PRIMARY KEY,
    bill_id BIGINT REFERENCES bills(bill_id),
    run_id VARCHAR(100) NOT NULL,  -- e.g., "ct_2025_20250129_143022"
    is_relevant BOOLEAN NOT NULL,
    reason TEXT,
    filtered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, run_id)
);

CREATE INDEX idx_filter_run_id ON filter_results(run_id);
CREATE INDEX idx_filter_relevant ON filter_results(bill_id, is_relevant);
```

#### 3. `analysis_results` - Analysis pass results
```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    bill_id BIGINT REFERENCES bills(bill_id),
    run_id VARCHAR(100) NOT NULL,
    is_relevant BOOLEAN NOT NULL,
    relevance_reasoning TEXT,
    summary TEXT,
    bill_status VARCHAR(50),
    legislation_type VARCHAR(50),
    categories JSONB,  -- Array of policy categories
    tags JSONB,
    key_provisions JSONB,
    palliative_care_impact TEXT,
    exclusion_check JSONB,
    special_flags JSONB,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, run_id)
);

CREATE INDEX idx_analysis_run_id ON analysis_results(run_id);
CREATE INDEX idx_analysis_relevant ON analysis_results(is_relevant);
CREATE INDEX idx_analysis_categories ON analysis_results USING GIN(categories);
```

#### 4. `legiscan_cache` - LegiScan API response cache
```sql
CREATE TABLE legiscan_cache (
    bill_id BIGINT PRIMARY KEY,
    response_data JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- Optional TTL for cache invalidation
);

CREATE INDEX idx_cache_expires ON legiscan_cache(expires_at);
```

#### 5. `pipeline_runs` - Track pipeline execution history
```sql
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    stage VARCHAR(50) NOT NULL,  -- 'fetch', 'filter', 'analysis'
    state VARCHAR(2),
    year INT,
    status VARCHAR(20),  -- 'running', 'completed', 'failed'
    bills_processed INT,
    bills_relevant INT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

CREATE INDEX idx_runs_status ON pipeline_runs(status);
CREATE INDEX idx_runs_state_year ON pipeline_runs(state, year);
```

## Storage Abstraction Layer

### StorageProvider Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class StorageProvider(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def save_raw_data(self, filename: str, data: Dict[str, Any]) -> None:
        """Save raw bill data from LegiScan"""
        pass

    @abstractmethod
    def load_raw_data(self, filename: str) -> Dict[str, Any]:
        """Load raw bill data"""
        pass

    @abstractmethod
    def save_filtered_results(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save filter pass results"""
        pass

    @abstractmethod
    def load_filtered_results(self, run_id: str) -> Dict[str, Any]:
        """Load filter pass results"""
        pass

    @abstractmethod
    def save_analysis_results(self, run_id: str, relevant: List[Dict],
                             not_relevant: List[Dict]) -> None:
        """Save analysis pass results"""
        pass

    @abstractmethod
    def load_analysis_results(self, run_id: str) -> tuple[List[Dict], List[Dict]]:
        """Load analysis results (relevant, not_relevant)"""
        pass

    @abstractmethod
    def get_bill_from_cache(self, bill_id: int) -> Optional[Dict]:
        """Get cached LegiScan bill data"""
        pass

    @abstractmethod
    def save_bill_to_cache(self, bill_id: int, data: Dict) -> None:
        """Save LegiScan bill data to cache"""
        pass

    @abstractmethod
    def list_raw_files(self) -> List[str]:
        """List available raw data files"""
        pass
```

### Implementation Classes

#### LocalFileStorage
- Implements current file-based behavior
- Uses `data/` directory structure
- JSON serialization/deserialization
- Default backend for local development

#### AzureBlobStorage
- Uses Azure Blob Storage SDK
- Mirrors local directory structure in blob containers
- Connection via `AZURE_STORAGE_CONNECTION_STRING`
- Automatic retry and error handling

#### DatabaseStorage
- PostgreSQL connection via psycopg2
- Transactions for data consistency
- Optional dual-write to files for compatibility
- Connection via `DATABASE_CONNECTION_STRING`

## Configuration

### config.json

```json
{
  "storage": {
    "backend": "local",
    "local": {
      "data_directory": "data"
    },
    "azure_blob": {
      "connection_string_env": "AZURE_STORAGE_CONNECTION_STRING",
      "container_name": "legiscan-data"
    },
    "database": {
      "type": "postgresql",
      "connection_string_env": "DATABASE_CONNECTION_STRING",
      "enable_file_fallback": true,
      "pool_size": 5,
      "pool_max_overflow": 10
    }
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

### Environment Variables

**Local Development:**
```bash
# .env file
PORTKEY_API_KEY=your_portkey_key
LEGISCAN_API_KEY=your_legiscan_key
STORAGE_BACKEND=local  # Default, can be omitted
```

**Azure Development (Shared Database):**
```bash
# .env file
PORTKEY_API_KEY=your_portkey_key
LEGISCAN_API_KEY=your_legiscan_key
STORAGE_BACKEND=database
DATABASE_CONNECTION_STRING=postgresql://user:pass@server.postgres.database.azure.com/legiscan_data?sslmode=require
```

**Azure Production (Container Apps):**
```bash
# Set via Key Vault references in Container Apps configuration
PORTKEY_API_KEY=@Microsoft.KeyVault(SecretUri=https://kv-legiscan-prod.vault.azure.net/secrets/PORTKEY-API-KEY/)
LEGISCAN_API_KEY=@Microsoft.KeyVault(SecretUri=https://kv-legiscan-prod.vault.azure.net/secrets/LEGISCAN-API-KEY/)
DATABASE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=https://kv-legiscan-prod.vault.azure.net/secrets/DATABASE-CONNECTION-STRING/)
STORAGE_BACKEND=database
```

## Usage

### Local Execution (Unchanged)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run pipeline as usual
cd scripts
python fetch_legiscan_bills.py
python run_filter_pass.py ct_bills_2025.json
python run_analysis_pass.py

# Data stored in local data/ directory
```

### Azure Execution (Same Commands!)

```bash
# Set environment to use database
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://..."

# Run same commands - now uses PostgreSQL
cd scripts
python fetch_legiscan_bills.py
python run_filter_pass.py ct_bills_2025
python run_analysis_pass.py

# Data stored in Azure PostgreSQL
# Accessible to all team members
```

### Team Member Collaboration

**Scenario 1: Local Development with Shared Data**
```bash
# Team member A runs filter pass
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="..."
python run_filter_pass.py ct_bills_2025.json

# Team member B runs analysis pass (same run_id)
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="..."
python run_analysis_pass.py

# Both see same results in database
```

**Scenario 2: Azure Scheduled Jobs**
```bash
# Configure Container Apps with schedule
# No manual execution needed
# Results available to all team members via React UI
```

## Deployment Steps

### Phase 1: Storage Abstraction Layer (Week 1-2)

**1.1 Create Storage Provider**
```bash
# Create new files
touch src/storage_provider.py
touch src/local_file_storage.py
touch src/azure_blob_storage.py
touch src/database_storage.py

# Implement abstract base class and providers
```

**1.2 Update Core Scripts**
```bash
# Modify to use StorageProvider
# Files to update:
# - src/ai_filter_pass.py
# - src/ai_analysis_pass.py
# - scripts/run_filter_pass.py
# - scripts/run_analysis_pass.py
# - scripts/run_direct_analysis.py
# - scripts/fetch_legiscan_bills.py
```

**1.3 Update Configuration**
```bash
# Add storage section to config.json
# Update config loading in scripts
```

**1.4 Test Local Execution**
```bash
# Verify identical behavior with STORAGE_BACKEND=local
cd scripts
python run_filter_pass.py ct_bills_2025.json
python run_analysis_pass.py

# Compare results with previous runs
diff data/analyzed/analysis_results_relevant.json <previous_results>
```

### Phase 2: Database Implementation (Week 2-3)

**2.1 Create Database Schema**
```bash
# Create infrastructure directory
mkdir -p infrastructure/migrations

# Create schema file
touch infrastructure/schema.sql

# Implement schema with all tables
```

**2.2 Set Up Local PostgreSQL (Testing)**
```bash
# Using Docker for local testing
docker run -d \
  --name legiscan-postgres \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=legiscan_data \
  -p 5432:5432 \
  postgres:15

# Apply schema
psql -h localhost -U postgres -d legiscan_data -f infrastructure/schema.sql
```

**2.3 Implement DatabaseStorage Provider**
```python
# src/database_storage.py
# - PostgreSQL connection pooling
# - CRUD operations for all tables
# - Transaction management
# - Error handling and retries
```

**2.4 Test Database Backend Locally**
```bash
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://postgres:testpass@localhost/legiscan_data"

cd scripts
python run_filter_pass.py ct_bills_2025.json
python run_analysis_pass.py

# Query database to verify
psql -h localhost -U postgres -d legiscan_data -c "SELECT COUNT(*) FROM bills;"
```

### Phase 3: Azure Infrastructure Setup (Week 3-4)

**3.1 Create Azure Resources**

Option A: Azure CLI
```bash
# Login
az login

# Create resource group
az group create --name rg-legiscan-prod --location eastus

# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group rg-legiscan-prod \
  --name legiscan-db-prod \
  --location eastus \
  --admin-user dbadmin \
  --admin-password <secure-password> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 15 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group rg-legiscan-prod \
  --server-name legiscan-db-prod \
  --database-name legiscan_data

# Create Key Vault
az keyvault create \
  --resource-group rg-legiscan-prod \
  --name kv-legiscan-prod \
  --location eastus

# Add secrets
az keyvault secret set --vault-name kv-legiscan-prod --name PORTKEY-API-KEY --value "your-key"
az keyvault secret set --vault-name kv-legiscan-prod --name LEGISCAN-API-KEY --value "your-key"
az keyvault secret set --vault-name kv-legiscan-prod --name DATABASE-CONNECTION-STRING --value "postgresql://..."

# Create Container Registry
az acr create \
  --resource-group rg-legiscan-prod \
  --name legiscanregistry \
  --sku Basic

# Create Container Apps Environment
az containerapp env create \
  --resource-group rg-legiscan-prod \
  --name legiscan-env \
  --location eastus
```

Option B: Terraform (Recommended)
```bash
# See infrastructure/terraform/ directory
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

**3.2 Apply Database Schema**
```bash
# Connect to Azure PostgreSQL
psql "host=legiscan-db-prod.postgres.database.azure.com port=5432 dbname=legiscan_data user=dbadmin password=<password> sslmode=require"

# Apply schema
\i infrastructure/schema.sql
```

**3.3 Build and Push Docker Image**
```bash
# Build container
docker build -t legiscan-pipeline:latest .

# Tag for Azure Container Registry
docker tag legiscan-pipeline:latest legiscanregistry.azurecr.io/legiscan-pipeline:latest

# Login to ACR
az acr login --name legiscanregistry

# Push image
docker push legiscanregistry.azurecr.io/legiscan-pipeline:latest
```

**3.4 Deploy Container App**
```bash
az containerapp create \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --environment legiscan-env \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --cpu 0.5 --memory 1.0Gi \
  --min-replicas 0 --max-replicas 1 \
  --secrets \
    portkey-key=keyvaultref:https://kv-legiscan-prod.vault.azure.net/secrets/PORTKEY-API-KEY,identityref:/subscriptions/.../managedIdentities/legiscan-identity \
    legiscan-key=keyvaultref:https://kv-legiscan-prod.vault.azure.net/secrets/LEGISCAN-API-KEY,identityref:/subscriptions/.../managedIdentities/legiscan-identity \
    db-connection=keyvaultref:https://kv-legiscan-prod.vault.azure.net/secrets/DATABASE-CONNECTION-STRING,identityref:/subscriptions/.../managedIdentities/legiscan-identity \
  --env-vars \
    PORTKEY_API_KEY=secretref:portkey-key \
    LEGISCAN_API_KEY=secretref:legiscan-key \
    DATABASE_CONNECTION_STRING=secretref:db-connection \
    STORAGE_BACKEND=database
```

### Phase 4: React UI Deployment (Week 4)

**4.1 Create API Backend**
```bash
cd legiUI
mkdir -p api

# Create API functions
touch api/bills.ts
touch api/filter-results.ts
touch api/analysis-results.ts
```

**4.2 Update UI to Use Database API**
```typescript
// src/services/api.ts
export async function fetchAnalyzedBills(state: string, year: number) {
  const response = await fetch(`/api/bills?state=${state}&year=${year}`);
  return response.json();
}
```

**4.3 Deploy to Azure Static Web Apps**
```bash
# Install Azure Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

# Build production bundle
npm run build

# Deploy
az staticwebapp create \
  --resource-group rg-legiscan-prod \
  --name legiscan-ui \
  --source . \
  --location eastus2 \
  --branch main \
  --app-location "legiUI" \
  --output-location "dist"
```

### Phase 5: Data Migration (Week 5)

**5.1 Create Migration Script**
```python
# scripts/migrate_to_database.py
# - Read all JSON files from data/
# - Insert into PostgreSQL tables
# - Validate data integrity
```

**5.2 Run Migration**
```bash
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://..."

cd scripts
python migrate_to_database.py

# Verify migration
python -c "
from database_storage import DatabaseStorage
storage = DatabaseStorage()
bills = storage.load_raw_data('ct_bills_2025')
print(f'Migrated {len(bills)} bills')
"
```

**5.3 Validate Results**
```bash
# Compare file-based vs database results
# Run analysis with both backends
# Ensure identical output
```

### Phase 6: Monitoring & Operations (Week 6)

**6.1 Set Up Application Insights**
```bash
# Create Application Insights
az monitor app-insights component create \
  --resource-group rg-legiscan-prod \
  --app legiscan-insights \
  --location eastus

# Connect to Container Apps and Static Web Apps
```

**6.2 Configure Alerts**
```bash
# Create alerts for:
# - Pipeline failures
# - API rate limit errors
# - Database connection issues
# - High API costs
```

**6.3 Create Scheduled Jobs**
```bash
# Configure Container Apps scheduled triggers
# Example: Daily run at 2 AM UTC
az containerapp job create \
  --resource-group rg-legiscan-prod \
  --name legiscan-daily-job \
  --environment legiscan-env \
  --trigger-type Schedule \
  --cron-expression "0 2 * * *" \
  --image legiscanregistry.azurecr.io/legiscan-pipeline:latest \
  --command "python /app/scripts/run_filter_pass.py ct_bills_2025.json && python /app/scripts/run_analysis_pass.py"
```

## Dual-Write Mode

During migration, enable dual-write to validate database implementation:

```json
// config.json
{
  "storage": {
    "backend": "database",
    "database": {
      "enable_file_fallback": true  // Writes to both DB and files
    }
  }
}
```

Benefits:
- Compare database vs file results
- Safety net during migration
- Easy rollback if issues arise
- Gradual confidence building

## Security Considerations

### 1. Secrets Management
- ✅ Never commit API keys or connection strings to Git
- ✅ Use Azure Key Vault for all secrets
- ✅ Rotate keys regularly
- ✅ Use managed identities for Container Apps

### 2. Database Security
- ✅ Enforce SSL connections (`sslmode=require`)
- ✅ Use strong passwords (20+ characters)
- ✅ Restrict firewall rules to known IPs
- ✅ Enable audit logging
- ✅ Regular backups (automated daily)

### 3. Network Security
- ✅ Container Apps in virtual network (optional)
- ✅ Private endpoints for PostgreSQL (recommended for production)
- ✅ Azure Front Door for Static Web Apps (optional)

### 4. Access Control
- ✅ Azure RBAC for resource access
- ✅ Database roles with least privilege
- ✅ Separate dev/staging/prod environments

## Cost Optimization

### Development Environment
- Use Burstable tier PostgreSQL (B1ms)
- Scale Container Apps to 0 when idle
- Use Free tier Static Web Apps
- Estimated: **$10-20/month**

### Production Environment
- Consider General Purpose PostgreSQL for performance (GP_Gen5_2)
- Use reserved capacity for 1-year savings (37% discount)
- Monitor AI API costs (largest variable cost)
- Set spending alerts
- Estimated: **$50-150/month** (depending on AI usage)

### Cost Monitoring
```bash
# Set up cost alerts
az consumption budget create \
  --resource-group rg-legiscan-prod \
  --budget-name legiscan-monthly-budget \
  --amount 100 \
  --time-grain Monthly \
  --start-date 2025-02-01 \
  --end-date 2026-01-31
```

## Troubleshooting

### Issue: Scripts can't connect to Azure PostgreSQL

**Solution:**
```bash
# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group rg-legiscan-prod \
  --name legiscan-db-prod

# Add your IP if needed
az postgres flexible-server firewall-rule create \
  --resource-group rg-legiscan-prod \
  --name legiscan-db-prod \
  --rule-name AllowMyIP \
  --start-ip-address <your-ip> \
  --end-ip-address <your-ip>
```

### Issue: Container App fails to start

**Solution:**
```bash
# Check logs
az containerapp logs show \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --follow

# Check environment variables
az containerapp show \
  --resource-group rg-legiscan-prod \
  --name legiscan-pipeline \
  --query properties.template.containers[0].env
```

### Issue: Database migrations fail

**Solution:**
```bash
# Check PostgreSQL logs
az postgres flexible-server server-logs list \
  --resource-group rg-legiscan-prod \
  --server-name legiscan-db-prod

# Download specific log
az postgres flexible-server server-logs download \
  --resource-group rg-legiscan-prod \
  --server-name legiscan-db-prod \
  --name <log-file-name>
```

### Issue: High database costs

**Solution:**
- Review query performance (use `EXPLAIN ANALYZE`)
- Add missing indexes
- Consider downgrading SKU for development
- Enable query performance insights
- Archive old data

## Maintenance

### Regular Tasks

**Daily:**
- Monitor pipeline execution logs
- Check for API errors
- Review Application Insights metrics

**Weekly:**
- Review cost reports
- Check database size and growth
- Analyze query performance
- Review failed analyses

**Monthly:**
- Rotate API keys
- Update dependencies
- Review and archive old data
- Optimize database indexes
- Check for security updates

### Backup Strategy

**Database Backups:**
- Automated daily backups (Azure PostgreSQL default)
- 7-day retention for point-in-time recovery
- Consider longer retention for compliance

**Export Data:**
```bash
# Export to JSON for archival
python scripts/export_to_json.py --run-id ct_2025_20250129

# Create database dump
pg_dump -h legiscan-db-prod.postgres.database.azure.com \
  -U dbadmin -d legiscan_data -F c -f legiscan_backup.dump
```

## Testing Strategy

### Unit Tests
```bash
# Test storage providers
pytest tests/test_storage_provider.py

# Test database operations
pytest tests/test_database_storage.py

# Test Azure Blob operations
pytest tests/test_azure_blob_storage.py
```

### Integration Tests
```bash
# Test full pipeline with database backend
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://test..."
pytest tests/integration/test_pipeline_database.py
```

### End-to-End Tests
```bash
# Test complete workflow
./tests/e2e/run_pipeline_test.sh
```

## Documentation Updates

After implementation, update these files:
- `README.md` - Add Azure deployment section
- `CLAUDE.md` - Document new storage configuration
- `docs/ARCHITECTURE.md` - Update architecture diagrams
- `docs/CONFIGURATION.md` - Add storage backend options

## Team Training

### Onboarding New Team Members

1. **Local Setup** (15 minutes)
   - Clone repository
   - Install dependencies
   - Configure .env with local backend
   - Run test pipeline

2. **Azure Access** (30 minutes)
   - Grant Azure RBAC permissions
   - Provide database connection string
   - Configure STORAGE_BACKEND=database
   - Test shared data access

3. **React UI Access** (5 minutes)
   - Share Static Web App URL
   - Demonstrate analysis browsing
   - Explain data refresh schedule

### Best Practices for Team

- **Local Development**: Always use `STORAGE_BACKEND=local` for testing
- **Shared Analysis**: Use `STORAGE_BACKEND=database` for team collaboration
- **Run IDs**: Use descriptive run_ids (e.g., `ct_2025_john_test_20250129`)
- **API Keys**: Never share personal API keys; use team Key Vault
- **Costs**: Be mindful of AI API usage in batch processing

## Future Enhancements

### Short Term (3-6 months)
- Add API for triggering pipeline via HTTP
- Implement webhook notifications for completed runs
- Create admin dashboard for pipeline management
- Add data export to CSV/Excel

### Long Term (6-12 months)
- Support for multiple state concurrent processing
- ML model for improved filtering (reduce AI API costs)
- Advanced analytics and trend analysis
- Real-time bill monitoring with notifications

## Support and Contact

For issues or questions:
- **Documentation**: Check `docs/` directory
- **GitHub Issues**: Report bugs and feature requests
- **Team Chat**: [Your team communication channel]

## Appendix

### A. Terraform Configuration Example

See `infrastructure/terraform/main.tf`

### B. Dockerfile Example

See `Dockerfile` in project root

### C. GitHub Actions CI/CD

See `.github/workflows/deploy.yml`

### D. Sample Database Queries

```sql
-- Get all relevant bills for Connecticut 2025
SELECT b.bill_number, b.title, a.categories
FROM bills b
JOIN analysis_results a ON b.bill_id = a.bill_id
WHERE b.state = 'CT'
  AND b.year = 2025
  AND a.is_relevant = true
ORDER BY b.bill_number;

-- Summary statistics by category
SELECT
  jsonb_array_elements_text(categories) as category,
  COUNT(*) as bill_count
FROM analysis_results
WHERE is_relevant = true
GROUP BY category
ORDER BY bill_count DESC;

-- Pipeline execution history
SELECT
  run_id,
  stage,
  status,
  bills_processed,
  bills_relevant,
  EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 10;
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-29
**Maintained By**: Development Team
