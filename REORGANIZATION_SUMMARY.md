# Directory Reorganization - October 2025

## Summary

The project has been reorganized to reflect its focus on **LegiScan state legislation analysis** for palliative care policy tracking, moving away from the original Federal Register approach.

## New Directory Structure

```
ai-scraper-ideas/
├── README.md                          # Main project documentation
├── requirements.txt                   # Python dependencies
├── .env / .env.example               # Environment configuration
├── .gitignore                        # Updated to exclude archive/
├── config.json / config.example.json # Active configuration
│
├── data/                             # All data files (gitignored)
│   ├── raw/                         # Raw LegiScan bill data
│   │   ├── ct_bills_2024.json
│   │   └── ct_bills_2025.json
│   ├── filtered/                    # Filter pass results
│   │   ├── filter_results_ct_bills_2024.json
│   │   └── filter_results_ct_bills_2025.json
│   ├── analyzed/                    # Analysis pass results
│   │   ├── analysis_results_relevant.json
│   │   └── analysis_results_not_relevant.json
│   └── cache/                       # LegiScan API cache
│       └── legiscan_cache/
│
├── scripts/                          # Executable scripts
│   ├── fetch_legiscan_bills.py      # Fetch bills from LegiScan API
│   ├── run_filter_pass.py           # First pass: filter bills
│   └── run_analysis_pass.py         # Second pass: analyze with full text
│
├── src/                              # Core library code
│   ├── ai_filter_pass.py            # Filter pass implementation
│   ├── ai_analysis_pass.py          # Analysis pass implementation
│   └── data_source_plugins.py       # Data source plugins
│
├── prompts/                          # Active AI prompts
│   ├── filter_prompt.md             # Filter pass prompt
│   ├── analysis_prompt.md           # Analysis pass prompt
│   └── system_prompt.md             # System instructions
│
├── config_examples/                  # Example configurations
│   ├── config_example.json
│   ├── config_database_example.json
│   ├── config_legiscan_example.json
│   └── config_plugins_example.json
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── AI_PROCESSOR_README.md
│   └── PLUGINS_README.md
│
└── archive/                          # Archived files (gitignored)
    ├── federal_register/            # Original Federal Register project
    │   ├── federal_register_importer.py
    │   ├── ai_data_processor.py
    │   ├── federal_register_output_*.json
    │   └── README.md
    ├── old_prompts/                 # Old/backup prompt versions
    │   ├── analysis_prompt_generic.md
    │   ├── analysis_prompt_palliative_care.md
    │   ├── system_prompt_palliative_care.md
    │   └── filter_prompt_bakup.md
    ├── test_files/                  # Test and temporary files
    │   ├── test.txt
    │   ├── test_samples.txt
    │   ├── test_run.log
    │   ├── test_api.py
    │   ├── test_filter.py
    │   ├── test_analysis.py
    │   └── test_analysis_results.json
    └── misc/                        # Other archived files
        ├── convert_to_text.py
        └── docker-compose.yml
```

## Key Changes

### Scripts Renamed and Moved
- `test_filter.py` → `scripts/run_filter_pass.py`
- `test_analysis.py` → `scripts/run_analysis_pass.py`
- `fetch_legiscan_bills.py` → `scripts/fetch_legiscan_bills.py`

### Path Updates
All scripts have been updated to use the new directory structure:
- Imports now reference `src/` modules
- Data files read from/write to `data/` subdirectories
- Prompts loaded from `prompts/` directory
- Cache stored in `data/cache/legiscan_cache/`

### Running Scripts

**Filter Pass:**
```bash
cd scripts
python run_filter_pass.py [input_file.json]
# Reads from: data/raw/
# Writes to: data/filtered/
```

**Analysis Pass:**
```bash
cd scripts
python run_analysis_pass.py
# Reads from: data/filtered/ and data/raw/
# Writes to: data/analyzed/
# Caches to: data/cache/legiscan_cache/
```

## What Was Archived

### Federal Register Project
- `federal_register_importer.py` - Original EPA scraper
- `ai_data_processor.py` - Generic processor
- Output files from Federal Register runs

### Old Prompts
- Generic and backup versions of prompts
- Previous palliative care prompt iterations

### Test Files
- Large test text files (921KB duplicates)
- Old test logs and scripts
- Previous test output files

### Miscellaneous
- `convert_to_text.py` - Text conversion utility
- `docker-compose.yml` - Docker configuration

## Benefits

1. **Clear Project Focus**: LegiScan state legislation analysis
2. **Organized Data**: Separated by processing stage (raw → filtered → analyzed)
3. **Clean Root**: Minimal files in root directory
4. **Preserved History**: All old files archived, nothing deleted
5. **Easy Git Management**: Archive directory gitignored

## Next Steps

1. Update README.md to reflect LegiScan focus
2. Test scripts with new paths
3. Consider adding data/ directory READMEs explaining each subdirectory
4. Document the two-pass pipeline workflow
