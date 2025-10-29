# Local vs Azure Usage Guide

## Overview

The LegiScan Bill Analysis Pipeline works **identically** in both local and Azure environments. The only difference is where data is stored.

---

## Quick Comparison

| Feature | Local (Default) | Azure Database | Azure Blob Storage |
|---------|----------------|----------------|-------------------|
| **Storage** | Local files (`data/`) | PostgreSQL database | Azure Blob Storage |
| **Setup** | None (works out of box) | Set 2 env vars | Set 2 env vars |
| **Commands** | Same | Same | Same |
| **Team Access** | ❌ No (local only) | ✅ Yes (shared DB) | ✅ Yes (shared blobs) |
| **Queryable** | ❌ No (files only) | ✅ Yes (SQL queries) | ❌ No (files only) |
| **Cost** | Free | ~$15-30/month | ~$0.50-2/month |
| **Best For** | Development, testing | Team collaboration | File archival |

---

## Local Usage (Default)

### Setup

**No setup needed!** Works exactly as it did before.

### Environment Variables

```bash
# Optional - this is the default
export STORAGE_BACKEND=local
```

### Commands

```bash
cd scripts

# Fetch bills from LegiScan
python fetch_legiscan_bills.py --state CT --year 2025

# Filter bills (first pass)
python run_filter_pass.py ct_bills_2025.json

# Analyze bills (second pass)
python run_analysis_pass.py

# Direct analysis (bypass filter)
python run_direct_analysis.py ../data/filtered/filter_results_ct_bills_2025.json
```

### Data Storage

```
data/
├── raw/
│   └── ct_bills_2025.json          # Fetched bills
├── filtered/
│   └── filter_results_ct_bills_2025.json  # Filter results
├── analyzed/
│   ├── analysis_results_relevant.json     # Relevant bills
│   └── analysis_results_not_relevant.json # Not relevant
└── cache/
    └── legiscan_cache/
        └── bill_*.json              # Cached API responses
```

### When to Use

- ✅ **Development** - Fast iteration, no cloud dependencies
- ✅ **Testing** - Quick tests without network latency
- ✅ **Personal Use** - Single user, no need for sharing
- ✅ **Offline Work** - No internet required (except API calls)

### Pros

- ✅ No configuration needed
- ✅ No cloud costs
- ✅ Fast (no network latency)
- ✅ Works offline (after initial fetch)
- ✅ Easy to inspect files

### Cons

- ❌ Not shared with team
- ❌ Can't query with SQL
- ❌ Manual file management
- ❌ No automatic backups

---

## Azure Database Usage (PostgreSQL)

### Setup

1. **Create Azure PostgreSQL Database** (one-time)
   ```bash
   az postgres flexible-server create \
     --resource-group rg-legiscan \
     --name legiscan-db \
     --location eastus \
     --admin-user dbadmin \
     --admin-password <secure-password> \
     --sku-name Standard_B1ms
   ```

2. **Apply Database Schema** (one-time)
   ```bash
   psql -h legiscan-db.postgres.database.azure.com \
        -U dbadmin \
        -d postgres \
        -f infrastructure/schema.sql
   ```

3. **Set Environment Variables** (each session)
   ```bash
   export STORAGE_BACKEND=database
   export DATABASE_CONNECTION_STRING="postgresql://dbadmin:password@legiscan-db.postgres.database.azure.com/legiscan_data?sslmode=require"
   ```

### Commands

**Exactly the same as local!**

```bash
cd scripts

# Same commands, different storage
python fetch_legiscan_bills.py --state CT --year 2025
python run_filter_pass.py ct_bills_2025
python run_analysis_pass.py
```

**Note**: File extensions (`.json`) are optional and automatically handled.

### Data Storage

```
Azure PostgreSQL Database: legiscan_data
├── bills                    # Raw bill data
├── filter_results          # Filter pass results
├── analysis_results        # Analysis pass results
├── legiscan_cache          # API response cache
└── pipeline_runs           # Execution history
```

### Query Examples

Since data is in PostgreSQL, you can run SQL queries:

```sql
-- Get all relevant bills for Connecticut 2025
SELECT b.bill_number, b.title, a.categories
FROM bills b
JOIN analysis_results a ON b.bill_id = a.bill_id
WHERE b.state = 'CT'
  AND b.year = 2025
  AND a.is_relevant = true
ORDER BY b.bill_number;

-- Category distribution
SELECT
  jsonb_array_elements_text(categories) as category,
  COUNT(*) as bill_count
FROM analysis_results
WHERE is_relevant = true
GROUP BY category
ORDER BY bill_count DESC;

-- Pipeline execution history
SELECT run_id, stage, status, bills_processed, bills_relevant
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 10;
```

### When to Use

- ✅ **Team Collaboration** - Multiple users need access to same data
- ✅ **Production** - Shared database for team workflows
- ✅ **Advanced Analysis** - SQL queries on bill data
- ✅ **Auditing** - Track who ran what when (pipeline_runs table)

### Pros

- ✅ Shared data across team
- ✅ SQL queries for analysis
- ✅ Automatic backups (Azure)
- ✅ Transaction safety
- ✅ Execution history tracking

### Cons

- ❌ Monthly cost (~$15-30)
- ❌ Requires internet connection
- ❌ Initial setup needed
- ❌ Slower than local (network latency)

---

## Azure Blob Storage Usage

### Setup

1. **Create Azure Storage Account** (one-time)
   ```bash
   az storage account create \
     --resource-group rg-legiscan \
     --name legiscanstorage \
     --location eastus \
     --sku Standard_LRS
   ```

2. **Get Connection String** (one-time)
   ```bash
   az storage account show-connection-string \
     --resource-group rg-legiscan \
     --name legiscanstorage
   ```

3. **Set Environment Variables** (each session)
   ```bash
   export STORAGE_BACKEND=azure_blob
   export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=legiscanstorage;AccountKey=...;EndpointSuffix=core.windows.net"
   ```

### Commands

**Exactly the same as local!**

```bash
cd scripts
python fetch_legiscan_bills.py --state CT --year 2025
python run_filter_pass.py ct_bills_2025
python run_analysis_pass.py
```

### Data Storage

```
Azure Blob Container: legiscan-data
├── raw/
│   └── ct_bills_2025.json
├── filtered/
│   └── filter_results_ct_bills_2025.json
├── analyzed/
│   ├── analysis_ct_bills_2025_relevant.json
│   └── analysis_ct_bills_2025_not_relevant.json
└── cache/
    └── legiscan_cache/
        └── bill_*.json
```

### When to Use

- ✅ **File Archival** - Long-term storage of bill data
- ✅ **Team File Sharing** - Share files without database
- ✅ **Cost Optimization** - Cheaper than database for large files
- ✅ **Hybrid Setup** - Blob for archives, DB for recent data

### Pros

- ✅ Shared file access
- ✅ Very cheap storage (~$0.50/month)
- ✅ Automatic redundancy (Azure LRS/GRS)
- ✅ Large file support

### Cons

- ❌ Not queryable (no SQL)
- ❌ Slower than local files
- ❌ No structured data benefits
- ❌ Requires internet connection

---

## Side-by-Side Command Comparison

### Fetching Bills

| Local | Azure Database | Azure Blob |
|-------|----------------|------------|
| `python fetch_legiscan_bills.py` | `python fetch_legiscan_bills.py` | `python fetch_legiscan_bills.py` |
| Saves to `data/raw/ct_bills_2025.json` | Saves to `bills` table | Saves to `raw/ct_bills_2025.json` blob |

### Filtering Bills

| Local | Azure Database | Azure Blob |
|-------|----------------|------------|
| `python run_filter_pass.py ct_bills_2025.json` | `python run_filter_pass.py ct_bills_2025` | `python run_filter_pass.py ct_bills_2025` |
| Reads from `data/raw/` | Reads from `bills` table | Reads from `raw/` blob |
| Saves to `data/filtered/` | Saves to `filter_results` table | Saves to `filtered/` blob |

### Analyzing Bills

| Local | Azure Database | Azure Blob |
|-------|----------------|------------|
| `python run_analysis_pass.py` | `python run_analysis_pass.py` | `python run_analysis_pass.py` |
| Reads from `data/filtered/` | Reads from `filter_results` table | Reads from `filtered/` blob |
| Saves to `data/analyzed/` | Saves to `analysis_results` table | Saves to `analyzed/` blob |

**Note**: Commands are identical! Only the storage backend changes.

---

## Switching Between Backends

You can switch between backends at any time by changing the environment variable:

```bash
# Use local files
export STORAGE_BACKEND=local
python run_filter_pass.py ct_bills_2025

# Switch to database
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://..."
python run_analysis_pass.py

# Switch to blob storage
export STORAGE_BACKEND=azure_blob
export AZURE_STORAGE_CONNECTION_STRING="..."
python run_filter_pass.py ct_bills_2025
```

### Configuration File Override

You can also set the default in `config.json`:

```json
{
  "storage": {
    "backend": "database"  // Change default backend
  }
}
```

Environment variables always override the configuration file.

---

## Hybrid Approach (Database + Files)

The `DatabaseStorage` provider supports **dual-write mode** for safe migration:

```json
{
  "storage": {
    "backend": "database",
    "database": {
      "enable_file_fallback": true  // Write to both DB and files
    }
  }
}
```

This allows you to:
- ✅ Gradually migrate to database
- ✅ Compare database vs file results
- ✅ Have safety net during transition
- ✅ Roll back if needed

---

## Team Collaboration Scenarios

### Scenario 1: Developer Working Locally

```bash
# Developer on local machine
export STORAGE_BACKEND=local
cd scripts
python run_filter_pass.py ct_bills_2025.json
# Results stay local
```

### Scenario 2: Team Sharing Database

```bash
# All team members set same env vars
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://..."

# Developer A runs filter pass
python run_filter_pass.py ct_bills_2025

# Developer B runs analysis pass (sees A's results)
python run_analysis_pass.py

# All results shared in database
```

### Scenario 3: Mixed Local + Database

```bash
# Developer tests locally
export STORAGE_BACKEND=local
python run_filter_pass.py test_bills

# Push results to database when ready
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="..."
python run_filter_pass.py ct_bills_2025  # Production run
```

---

## Environment Variable Reference

### Local Storage (Default)

```bash
# Optional - this is the default if not set
export STORAGE_BACKEND=local
```

**No other variables needed.**

### Azure Database Storage

```bash
# Required
export STORAGE_BACKEND=database
export DATABASE_CONNECTION_STRING="postgresql://user:password@server.postgres.database.azure.com/legiscan_data?sslmode=require"
```

**Connection String Format:**
```
postgresql://[user]:[password]@[host]:[port]/[database]?sslmode=require
```

### Azure Blob Storage

```bash
# Required
export STORAGE_BACKEND=azure_blob
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
```

**Connection String**: Get from Azure Portal or CLI

---

## Troubleshooting

### "Could not initialize storage provider"

**Cause**: Invalid configuration or missing dependencies

**Solution**:
```bash
# Verify config.json
python -c "import json; json.load(open('config.json'))"

# Verify dependencies
pip install -r requirements.txt
```

### "FileNotFoundError" with database backend

**Cause**: Using `.json` extension when not needed

**Solution**:
```bash
# Correct
python run_filter_pass.py ct_bills_2025

# Incorrect (don't include .json with database)
python run_filter_pass.py ct_bills_2025.json
```

### Database connection failed

**Cause**: Network issues or wrong connection string

**Solution**:
```bash
# Test connection
psql "$DATABASE_CONNECTION_STRING" -c "SELECT 1;"

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group rg-legiscan \
  --name legiscan-db
```

---

## Best Practices

### Development Workflow

1. **Develop Locally**
   ```bash
   export STORAGE_BACKEND=local
   # Fast iteration, no cloud costs
   ```

2. **Test with Database**
   ```bash
   export STORAGE_BACKEND=database
   # Verify database integration works
   ```

3. **Deploy to Production**
   ```bash
   # Azure Container Apps with database backend
   # Automated scheduled runs
   ```

### Team Workflow

1. **Individual Exploration**
   - Use `local` backend for testing ideas
   - No interference with team data

2. **Collaborative Analysis**
   - Switch to `database` backend
   - Share results with team

3. **Production Runs**
   - Use database backend
   - Track execution history
   - Team visibility

---

## Cost Comparison

| Backend | Setup Cost | Monthly Cost | Storage Limit |
|---------|-----------|--------------|---------------|
| Local | $0 | $0 | Disk space |
| Azure Database (B1ms) | $0 | ~$15-30 | 32 GB included |
| Azure Blob Storage (LRS) | $0 | ~$0.50-2 | Pay per GB (~$0.02/GB) |

**Recommendation**: Start with local, upgrade to database when sharing is needed.

---

## Summary

| Feature | Local | Database | Blob |
|---------|-------|----------|------|
| **Commands** | ✅ Same | ✅ Same | ✅ Same |
| **Setup** | ✅ None | ⚠️ One-time | ⚠️ One-time |
| **Team Access** | ❌ No | ✅ Yes | ✅ Yes |
| **SQL Queries** | ❌ No | ✅ Yes | ❌ No |
| **Cost** | ✅ Free | ⚠️ ~$20/mo | ✅ ~$1/mo |
| **Speed** | ✅ Fast | ⚠️ Network | ⚠️ Network |
| **Best For** | Development | Production | Archives |

**Key Takeaway**: The application works identically across all backends - just set the environment variable!

---

## Next Steps

1. **Read**: [QUICK_START.md](QUICK_START.md) for getting started
2. **Deploy**: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for full deployment guide
3. **Test**: Run `python scripts/test_storage_provider.py` to validate setup
4. **Choose**: Pick the backend that fits your needs (local for dev, database for team)

---

**Questions?** See the comprehensive deployment guide in [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).
