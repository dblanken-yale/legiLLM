# Federal Register → AI → Drupal POC

## Architecture Overview

```
┌─────────────────────┐
│ Federal Register API│
│   (Public JSON)     │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  Python Fetcher     │
│  - Query by criteria│
│  - Rate limiting    │
│  - Data extraction  │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  Portkey AI Gateway │
│  - Summarization    │
│  - Categorization   │
│  - Tag extraction   │
│  - Entity detection │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  Drupal JSON:API    │
│  - Create nodes     │
│  - Apply taxonomy   │
│  - Store metadata   │
└─────────────────────┘
```

## Data Flow

### 1. Fetch from Federal Register
```python
# Example query
GET /api/v1/documents.json?
  conditions[agencies][]=environmental-protection-agency&
  conditions[type][]=RULE&
  conditions[publication_date][gte]=2025-01-01&
  fields[]=title&
  fields[]=abstract&
  fields[]=body_html_url&
  per_page=20
```

### 2. AI Processing with Portkey
```python
# Send to Portkey for:
- Extract key topics/themes
- Generate executive summary
- Suggest taxonomy terms
- Identify stakeholders
- Assess impact level
```

### 3. Import to Drupal
```python
# POST to Drupal JSON:API
{
  "data": {
    "type": "node--federal_register_document",
    "attributes": {
      "title": "...",
      "field_document_number": "...",
      "field_agency": "...",
      "field_publication_date": "...",
      "field_original_abstract": "...",
      "field_ai_summary": "...",
      "field_full_text_url": "..."
    },
    "relationships": {
      "field_categories": {...},
      "field_tags": {...}
    }
  }
}
```

## Components

### Python Script (`federal_register_importer.py`)
- Fetch documents based on criteria
- Parse and extract relevant fields
- Call Portkey for AI enrichment
- Post to Drupal JSON:API
- Handle errors and logging

### Drupal Content Type (`federal_register_document`)
- Document number (unique identifier)
- Title
- Agency (taxonomy reference)
- Document type (RULE, NOTICE, etc.)
- Publication date
- Original abstract
- AI-generated summary
- AI-extracted categories/tags
- Full text URL
- PDF URL
- Metadata (JSON field)

### Configuration
- Search criteria (agencies, date ranges, document types)
- Portkey API key and model selection
- Drupal endpoint and credentials
- Processing schedule (cron)

## POC Goals

1. Successfully fetch 20+ documents from Federal Register API
2. Process through Portkey to generate summaries and categorization
3. Import into Drupal with proper content type structure
4. Validate data quality and AI accuracy
5. Measure performance and identify bottlenecks
