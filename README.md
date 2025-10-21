# Federal Register AI Scraper POC

Proof of concept for fetching Federal Register documents, processing with AI via Portkey, and importing to Drupal.

## Architecture

Federal Register API → Portkey AI → Drupal JSON:API

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

See [CONFIGURATION.md](CONFIGURATION.md) for complete configuration guide.

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

**Required:**
- `PORTKEY_API_KEY` - Your Portkey API key

**Optional (for Drupal integration):**
- `DRUPAL_URL` - Your Drupal site URL
- `DRUPAL_USER` - Drupal username
- `DRUPAL_PASS` - Drupal password

If Drupal credentials are not provided, the script will run in **fetch + AI mode only** and output results to a JSON file.

### 3. Create Drupal Content Type (Optional)

If you want to import to Drupal, create a content type `federal_register_document` with these fields:

- `field_document_number` (text, unique)
- `field_publication_date` (date)
- `field_document_type` (text)
- `field_agencies` (text, multi-value)
- `field_original_abstract` (text_long)
- `field_ai_summary` (text_long)
- `field_html_url` (link)
- `field_pdf_url` (link)
- `field_ai_categories` (text, multi-value)
- `field_ai_tags` (text, multi-value)
- `field_key_entities` (text, multi-value)

Enable JSON:API for this content type.

### 4. Configure Search Parameters (Optional)

Edit `config.json` to customize Federal Register queries and AI settings:

```json
{
  "federal_register": {
    "agencies": ["environmental-protection-agency"],
    "document_types": ["RULE", "PRORULE"],
    "start_date": "2025-01-01",
    "term": "climate",
    "limit": 20
  },
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 800
  }
}
```

**Federal Register Parameters:**
- `agencies`: List of agency slugs (see below for examples)
- `document_types`: RULE, PRORULE, NOTICE, PRESDOCU
- `start_date`: YYYY-MM-DD format (defaults to yesterday)
- `term`: Search term/keyword
- `limit`: Max documents to fetch

**AI Parameters:**
- `model`: OpenAI model to use via Portkey
- `temperature`: 0.0-1.0 (lower = more deterministic)
- `max_tokens`: Maximum response length

### 5. Customize AI Prompts (Optional)

Edit prompt templates to change how documents are analyzed:

- `prompts/system_prompt.md` - System instructions for the AI
- `prompts/analysis_prompt.md` - Task prompt template

The analysis prompt supports these variables:
- `{title}` - Document title
- `{doc_type_label}` - Document type
- `{content}` - Abstract or title+agencies

### 6. Run the Importer

```bash
python federal_register_importer.py
```

Results will be:
- Logged to console
- Written to `federal_register_output_YYYYMMDD_HHMMSS.json`
- Imported to Drupal (if credentials provided)

## Usage

Configuration is managed through `config.json`. See `config.example.json` for a full example.

### Available Agencies (examples)

- `environmental-protection-agency`
- `food-and-drug-administration`
- `securities-and-exchange-commission`
- `federal-communications-commission`
- `department-of-labor`

### Document Types

- `RULE` - Final rules
- `PRORULE` - Proposed rules
- `NOTICE` - Notices
- `PRESDOCU` - Presidential documents

## Components

### FederalRegisterFetcher
Fetches documents from Federal Register API with filtering.

### PortkeyAIProcessor
Sends documents to Portkey AI for:
- Executive summaries
- Category extraction
- Tag generation
- Entity recognition

### DrupalImporter
Posts enriched content to Drupal via JSON:API.

### FederalRegisterPipeline
Orchestrates the full pipeline.

## Next Steps

1. Add error recovery and retry logic
2. Implement duplicate detection
3. Add taxonomy term creation in Drupal
4. Build scheduling with cron/celery
5. Add monitoring and alerting
6. Enhance AI prompts for better categorization
7. Add support for full-text fetching from `body_html_url`

## Notes

- Federal Register API requires no authentication
- Rate limiting: Be respectful, add delays between requests
- Portkey acts as gateway to various AI models
- Drupal authentication uses basic auth + CSRF token
