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
```

### Two-Stage Pipeline

**Stage 1: Filter Pass** (`run_filter_pass.py`)
- Processes large datasets efficiently (50 bills per batch)
- Uses only title and metadata for quick filtering
- Identifies bills potentially relevant to palliative care
- Output: `data/filtered/filter_results_*.json`

**Stage 2: Analysis Pass** (`run_analysis_pass.py`)
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

```bash
cd scripts
python run_analysis_pass.py
```

Analyzes filtered bills with full text and outputs categorized results to `data/analyzed/`.

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
    "timeout": 90
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

#### LegiScan Settings (`legiscan`)
- `cache_enabled` - Whether to cache API responses (default: `true`)
- `cache_directory` - Path to cache directory (default: `data/cache/legiscan_cache`)

### Test Mode

To test with a small sample before running full analysis:

```bash
export TEST_MODE=true
export TEST_COUNT=5
python scripts/run_analysis_pass.py
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
│   ├── filtered/           # Filter pass results
│   ├── analyzed/           # Analysis pass results
│   └── cache/              # LegiScan API response cache
├── scripts/                # Executable scripts
│   ├── fetch_legiscan_bills.py
│   ├── run_filter_pass.py
│   └── run_analysis_pass.py
├── src/                    # Core library code
│   ├── ai_filter_pass.py
│   ├── ai_analysis_pass.py
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

### Hook System
- **Pluggable data enrichment**: Register custom hooks for pre/post processing
- **Configurable timing**: Execute hooks at specific pipeline points (pre_analysis, post_analysis, etc.)
- **Framework-level caching**: Automatic caching using item_id from context
- **LegiScan hook included**: Fetches full bill text from LegiScan API before analysis
- **Optional and flexible**: Enable/disable via config, easy to add custom hooks

### LegiScan Integration (via Hook)
- Fetches full bill text via `getBill` API endpoint
- File-based caching to avoid duplicate API calls
- Extracts bill number, title, description, status, sponsors, subjects
- Enabled by default in config.example.json

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
- Hook results cached in `data/cache/hooks/`
- LegiScan API responses cached in `data/cache/legiscan_cache/`
- One JSON file per item (keyed by item_id or bill_id)
- Automatic cache creation and loading
- Reduces API calls and speeds up re-runs

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
- [docs/HOOKS.md](docs/HOOKS.md) - Hook system for data enrichment

## Development

### Running Tests

Test mode processes a small sample (5 bills by default):

```bash
export TEST_MODE=true
python scripts/run_filter_pass.py
python scripts/run_analysis_pass.py
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

- **Hook System**: Flexible data enrichment via configurable hooks (see docs/HOOKS.md)
- **LegiScan API**: Requires API key, rate limits apply
- **Portkey Gateway**: Proxies requests to OpenAI and other AI providers
- **Caching**: All LegiScan responses and hook results are cached to minimize API calls
- **Two-stage approach**: Balances speed (filter pass) with accuracy (analysis pass)
- **Generic pipeline**: Core logic is data-source agnostic via hook system
- **No Drupal integration yet**: Future enhancement for content management

## Previous Version

The original Federal Register scraping project has been archived in `archive/federal_register/`. See `archive/federal_register/README.md` for details on the previous implementation.

## License

[Add your license here]
