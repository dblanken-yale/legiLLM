# LegiScan State Bill Analysis Pipeline

AI-powered two-stage pipeline for analyzing state legislation with focus on palliative care policy tracking.

## Overview

This project provides an automated pipeline for:
1. **Filter Pass**: Quickly filter thousands of state bills to identify potentially relevant legislation
2. **Analysis Pass**: Deep analysis of filtered bills using full text from LegiScan API
3. **Categorization**: Apply comprehensive policy framework with 8 palliative care categories
4. **Relevance Re-evaluation**: Confirm relevance using full bill text, not just metadata

## Architecture

```
LegiScan API → Filter Pass (metadata) → Analysis Pass (full text) → Categorized Results
                                    ↓
                        OR: Pre-filtered data → Direct Analysis → Categorized Results
```

### Two-Stage Pipeline

**Stage 1: Filter Pass** (`run_filter_pass.py`)
- Processes large datasets efficiently (50 bills per batch)
- Uses only title and metadata for quick filtering
- Identifies bills potentially relevant to palliative care
- Output: `data/filtered/filter_results_*.json`

**Alternative: Pre-filtered Data**
- External filtering methods (vector similarity, embeddings, etc.) can provide pre-filtered results
- Supports multiple filter formats (AI-filtered, vector similarity)
- Use `run_direct_analysis.py` to analyze pre-filtered data directly

**Stage 2: Analysis Pass** (`run_analysis_pass.py` or `run_direct_analysis.py`)
- Fetches full bill text from LegiScan API
- Re-evaluates relevance with complete bill content
- Applies 8-category palliative care policy framework
- Caches API responses to avoid re-fetching
- Output:
  - `data/analyzed/analysis_results_relevant.json`
  - `data/analyzed/analysis_results_not_relevant.json`

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required Environment Variables:**
- `PORTKEY_API_KEY` - Your Portkey API key (for AI analysis)
- `LEGISCAN_API_KEY` - Your LegiScan API key (for bill data)

### 3. Fetch State Bills

```bash
cd scripts
python fetch_legiscan_bills.py
```

This fetches bills from LegiScan and saves to `data/raw/ct_bills_2025.json`.

### 4. Run Filter Pass

```bash
cd scripts
python run_filter_pass.py
```

Processes bills in batches and outputs potentially relevant bills to `data/filtered/`.

### 5. Run Analysis Pass

**Option A: Standard Analysis** (for AI-filtered results from step 4)
```bash
cd scripts
python run_analysis_pass.py
```

**Option B: Direct Analysis** (for pre-filtered data from any source)
```bash
cd scripts
python run_direct_analysis.py <path_to_filter_results.json>

# Examples:
python run_direct_analysis.py ../data/filtered/filter_results_ct_bills_2025.json
python run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json
```

Both scripts analyze filtered bills with full text and output categorized results to `data/analyzed/`.

**When to use each:**
- Use `run_analysis_pass.py` when you've run the filter pass in step 4
- Use `run_direct_analysis.py` when you have pre-filtered data from external sources (vector similarity, embeddings, etc.)

## Configuration

### Basic Configuration

Create `config.json` in the project root (see `config_examples/` for templates):

```json
{
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

### Configuration Options

#### AI Model Settings
- `model` - OpenAI model via Portkey (default: `gpt-4o-mini`)
- `temperature` - Sampling temperature 0.0-1.0 (default: `0.3`)
- `max_tokens` - Maximum response length (default: `2000`)

#### Filter Pass Settings (`filter_pass`)
- `batch_size` - Number of bills to process per API call (default: `50`)
  - Higher values = fewer API calls but longer processing time per batch
  - Lower values = more API calls but faster feedback
- `timeout` - API request timeout in seconds (default: `180`)
  - Increase if batches are timing out
  - Filter pass processes multiple bills per request, needs longer timeout

#### Analysis Pass Settings (`analysis_pass`)
- `timeout` - API request timeout in seconds (default: `90`)
  - Increase if analysis requests are timing out with full bill text
  - Analysis pass processes one bill per request with full text
- `api_delay` - Delay between LegiScan API calls in seconds (default: `0.0`)
  - Set to `1.0` or higher to add rate limiting between API requests
  - Delay only applies to actual API calls, not cached responses
  - Useful to avoid hitting LegiScan API rate limits

#### LegiScan Settings (`legiscan`)
- `cache_enabled` - Whether to cache API responses (default: `true`)
- `cache_directory` - Path to cache directory (default: `data/cache/legiscan_cache`)

### Test Mode

To test with a small sample before running full analysis:

```bash
export TEST_MODE=true
export TEST_COUNT=5

# Standard analysis
python scripts/run_analysis_pass.py

# Or with direct analysis
python scripts/run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json
```

### Advanced Configuration

See `config_examples/` directory for example configurations:
- `config_example.json` - Complete configuration with all options
- `config_legiscan_example.json` - LegiScan integration examples
- `config_database_example.json` - Database integration examples
- `config_plugins_example.json` - Plugin system examples

All configuration options have sensible defaults. You can create a minimal `config.json` with just the settings you want to override:

```json
{
  "model": "gpt-4o",
  "filter_pass": {
    "batch_size": 100
  }
}
```

## Supported Filter Formats

The analysis pipeline supports multiple filter result formats, allowing you to use external filtering methods (vector similarity, embeddings, etc.) alongside the built-in AI filter.

### Format 1: AI-Filtered (Standard)

Output from `run_filter_pass.py`:

```json
{
  "summary": {
    "total_analyzed": 4014,
    "relevant_count": 68,
    "not_relevant_count": 3946,
    "source_file": "ct_bills_2025.json"
  },
  "relevant_bills": [
    {
      "bill_number": "SB01071",
      "title": "An Act Implementing The Recommendations...",
      "url": "https://legiscan.com/CT/bill/SB01071/2025",
      "reason": "Establishes pediatric hospice working group..."
    }
  ]
}
```

**Characteristics:**
- Contains `relevant_bills` array
- Includes `summary` with statistics
- Each bill has a `reason` field explaining why it was flagged

### Format 2: Vector Similarity

Output from external filtering tools (embeddings, semantic search):

```json
{
  "total_results": 8,
  "results": [
    {
      "bill_id": "1932259",
      "number": "SB01071",
      "title": "An Act Implementing The Recommendations...",
      "url": "https://legiscan.com/CT/bill/SB01071/2025",
      "status_date": "2025-01-22",
      "last_action": "Referred to Joint Committee...",
      "year": "2025",
      "session": "2025 Regular Session",
      "similarity_score": 0.524,
      "distance": 0.907
    }
  ]
}
```

**Characteristics:**
- Contains `results` array instead of `relevant_bills`
- Uses `number` instead of `bill_number`
- Includes similarity metrics (`similarity_score`, `distance`)
- Contains additional metadata (`status_date`, `last_action`, `year`, `session`)

### Using Different Formats

The `run_direct_analysis.py` script automatically detects and normalizes both formats:

```bash
# Works with AI-filtered format
python run_direct_analysis.py ../data/filtered/filter_results_ct_bills_2025.json

# Works with vector similarity format
python run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json
```

**Format Detection:**
- Checks for `relevant_bills` (Format 1) vs `results` (Format 2)
- Normalizes field names (`number` → `bill_number`)
- Preserves extra metadata in output (similarity scores, status info)
- Uses `bill_number` to lookup full bill data from source file

## Palliative Care Policy Framework

### 8 Policy Categories

Bills are categorized into one or more of these areas:

1. **Clinical Skill-Building** - Education and training for healthcare providers
2. **Patient Rights** - Advance directives, POLST, informed consent
3. **Payment** - Insurance coverage, Medicaid, reimbursement
4. **Pediatric Palliative Care** - Concurrent care for children
5. **Public Awareness** - Education campaigns, community outreach
6. **Quality/Standards** - Best practices, quality measures, certification
7. **Telehealth** - Remote palliative care delivery
8. **Workforce** - Recruitment, retention, workforce development

### Exclusion Criteria

The analysis explicitly excludes:
- Aid-in-dying/death with dignity legislation
- General adult hospice (unless pediatric concurrent care)
- Medical marijuana and psilocybin therapies

### Bill Status Tracking

- **Enacted**: Passed into law
- **Failed**: Failed to pass
- **Pending**: Currently under consideration
- **Vetoed**: Vetoed by governor
- **Unknown**: Status cannot be determined

## Project Structure

```
ai-scraper-ideas/
├── data/                    # All data files (gitignored)
│   ├── raw/                # Raw LegiScan bill data
│   ├── filtered/           # Filter pass results (multiple formats supported)
│   ├── analyzed/           # Analysis pass results
│   └── cache/              # LegiScan API response cache
├── scripts/                # Executable scripts
│   ├── fetch_legiscan_bills.py
│   ├── run_filter_pass.py
│   ├── run_analysis_pass.py
│   └── run_direct_analysis.py  # Dual-format analysis support
├── src/                    # Core library code
│   ├── ai_filter_pass.py
│   ├── ai_analysis_pass.py
│   ├── format_normalizer.py    # Format detection and normalization
│   └── data_source_plugins.py
├── prompts/                # AI prompt templates
│   ├── filter_prompt.md
│   ├── analysis_prompt.md
│   └── system_prompt.md
├── config_examples/        # Example configurations
├── docs/                   # Documentation
└── archive/                # Archived Federal Register project
```

## Customizing Prompts

Edit prompt templates to change how bills are analyzed:

- `prompts/system_prompt.md` - Palliative care expertise and guidelines
- `prompts/filter_prompt.md` - First pass filtering criteria
- `prompts/analysis_prompt.md` - Detailed categorization framework

The analysis prompt includes:
- Relevance determination with full text
- 8-category framework with detailed definitions
- Bill status identification
- Exclusion criteria checks
- Structured JSON output format

## Output Format

### Filter Pass Output

```json
{
  "summary": {
    "total_analyzed": 4064,
    "relevant_count": 68,
    "not_relevant_count": 3996
  },
  "relevant_bills": [
    {
      "bill_number": "SB01540",
      "title": "An Act Implementing The Recommendations...",
      "url": "https://legiscan.com/CT/bill/SB01540/2025",
      "reason": "Establishes pediatric hospice working group..."
    }
  ]
}
```

### Analysis Pass Output

```json
{
  "bill": {
    "bill_number": "SB01540",
    "title": "An Act Implementing The Recommendations..."
  },
  "analysis": {
    "is_relevant": true,
    "relevance_reasoning": "Bill directly addresses pediatric palliative care...",
    "summary": "Implements pediatric hospice working group recommendations...",
    "bill_status": "Enacted",
    "legislation_type": "Bill",
    "categories": ["Pediatric Palliative Care", "Quality/Standards"],
    "tags": ["pediatric", "concurrent care", "medicaid"],
    "key_provisions": [
      "Concurrent curative and palliative care for children",
      "Medicaid coverage expansion"
    ],
    "palliative_care_impact": "...",
    "exclusion_check": {
      "is_excluded": false,
      "reason": "Pediatric hospice exception applies"
    }
  }
}
```

## Features

### Multiple Filter Format Support
- **AI-filtered format**: Output from `run_filter_pass.py` with reasoning
- **Vector similarity format**: Output from external tools with similarity scores
- **Auto-detection**: `run_direct_analysis.py` automatically detects and normalizes formats
- **Preserved metadata**: Similarity scores and extra fields stored in output

### LegiScan Integration
- Fetches full bill text via `getBill` API endpoint
- File-based caching to avoid duplicate API calls
- Configurable API delay for rate limiting
- Extracts bill number, title, description, status, sponsors, subjects

### Batch Processing
- Filter pass processes 50 bills per API call
- Configurable batch size and timeout
- Progress tracking and error handling

### Relevance Re-evaluation
- First pass: Quick filter on metadata (fast, cheap)
- Second pass: Deep analysis with full text (thorough, accurate)
- Catches false positives from first pass
- Provides reasoning for inclusion/exclusion decisions

### Caching
- LegiScan API responses cached in `data/cache/legiscan_cache/`
- One JSON file per bill (keyed by bill_id)
- Automatic cache creation and loading
- Reduces API calls and speeds up re-runs
- Respects cache when applying API delay (no delay for cached bills)

## API Keys

### Portkey API
Get your API key from [Portkey.ai](https://portkey.ai)
```bash
export PORTKEY_API_KEY='your-key-here'
```

### LegiScan API
Get your API key from [LegiScan.com](https://legiscan.com/legiscan)
```bash
export LEGISCAN_API_KEY='your-key-here'
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture and design
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Complete configuration guide
- [docs/AI_PROCESSOR.md](docs/AI_PROCESSOR.md) - AI processing details
- [docs/PLUGINS.md](docs/PLUGINS.md) - Data source plugins

## Development

### Running Tests

Test mode processes a small sample (5 bills by default):

```bash
export TEST_MODE=true
export TEST_COUNT=5

# Test filter pass
python scripts/run_filter_pass.py

# Test standard analysis
python scripts/run_analysis_pass.py

# Test direct analysis with pre-filtered data
python scripts/run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json
```

### Adding New States

Edit `scripts/fetch_legiscan_bills.py` to fetch bills from different states:

```python
state = 'NY'  # Change to desired state code
year = 2025
```

### Customizing Categories

Edit `prompts/analysis_prompt.md` to add or modify policy categories for your use case.

## Notes

- **LegiScan API**: Requires API key, rate limits apply (use `api_delay` config for rate limiting)
- **Portkey Gateway**: Proxies requests to OpenAI and other AI providers
- **Caching**: All LegiScan responses are cached to minimize API calls
- **Two-stage approach**: Balances speed (filter pass) with accuracy (analysis pass)
- **Multiple filter formats**: Supports both AI-filtered and vector similarity formats
- **External filtering**: You can use any filtering method (embeddings, semantic search, etc.) as long as the output follows one of the supported formats
- **No Drupal integration yet**: Future enhancement for content management

## Previous Version

The original Federal Register scraping project has been archived in `archive/federal_register/`. See `archive/federal_register/README.md` for details on the previous implementation.

## License

[Add your license here]
