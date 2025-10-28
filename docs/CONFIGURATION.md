# Configuration Guide

The Federal Register importer can be fully configured through JSON and Markdown files.

## Configuration Files

### `config.json` - Main Configuration

Controls Federal Register API queries and AI model settings.

```json
{
  "federal_register": {
    "agencies": ["environmental-protection-agency"],
    "document_types": ["RULE", "PRORULE", "NOTICE"],
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

#### Federal Register Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `agencies` | array | List of agency slugs to filter by | `[]` (all agencies) |
| `document_types` | array | Types: RULE, PRORULE, NOTICE, PRESDOCU | `[]` (all types) |
| `start_date` | string | Start date in YYYY-MM-DD format | Yesterday |
| `term` | string | Search term for full-text search | `null` (no search) |
| `limit` | number | Maximum documents to fetch | `10` |

**Common Agency Slugs:**
- `environmental-protection-agency`
- `food-and-drug-administration`
- `securities-and-exchange-commission`
- `federal-communications-commission`
- `department-of-labor`
- `department-of-health-and-human-services`
- `department-of-energy`
- `department-of-agriculture`

Find more at: https://www.federalregister.gov/agencies

#### AI Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | string | OpenAI model via Portkey | `gpt-4o-mini` |
| `temperature` | number | 0.0-1.0 (lower = more consistent) | `0.3` |
| `max_tokens` | number | Maximum response length | `800` |

### `prompts/system_prompt.md` - System Instructions

Defines the AI's role and behavior. This is the "system" message sent to the model.

**Example:**
```markdown
# System Prompt for Federal Register Document Analysis

You are an expert at analyzing federal regulatory documents. 

Your role is to:
- Provide structured, accurate analysis of government documents
- Extract key information efficiently
- Categorize documents using relevant, specific categories
- Identify important entities, organizations, and stakeholders
- Generate clear, concise summaries

Guidelines:
- Be factual and objective
- Focus on the most important aspects of each document
- Use consistent categorization across similar document types
- Identify all relevant government agencies and entities
```

### `prompts/analysis_prompt.md` - Analysis Task

Defines the specific task and output format. Supports template variables.

**Available Variables:**
- `{title}` - Document title
- `{doc_type_label}` - Document type (e.g., "Document Type: Proposed Rule\n")
- `{content}` - Abstract text, or title+type+agencies if no abstract

**Example:**
```markdown
# Analysis Task Prompt

Analyze this Federal Register document and provide:

1. **Executive Summary**: A concise 2-3 sentence summary
2. **Categories**: Up to 5 relevant high-level categories
3. **Tags**: Up to 10 specific tags/keywords
4. **Key Entities**: Important agencies, organizations, locations

## Document Information

**Title**: {title}
{doc_type_label}**Content**: {content}

## Response Format

Respond ONLY with valid JSON:
{{
  "summary": "...",
  "categories": ["...", "..."],
  "tags": ["...", "..."],
  "key_entities": ["...", "..."]
}}
```

## Configuration Examples

### Example 1: Recent EPA Environmental Rules

```json
{
  "federal_register": {
    "agencies": ["environmental-protection-agency"],
    "document_types": ["RULE", "PRORULE"],
    "start_date": "2025-01-01",
    "term": "climate",
    "limit": 50
  },
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "max_tokens": 1000
  }
}
```

### Example 2: FDA Notices (Last 30 Days)

```json
{
  "federal_register": {
    "agencies": ["food-and-drug-administration"],
    "document_types": ["NOTICE"],
    "start_date": "2025-09-21",
    "term": null,
    "limit": 100
  },
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 800
  }
}
```

### Example 3: All Recent Documents (No Filters)

```json
{
  "federal_register": {
    "agencies": [],
    "document_types": [],
    "start_date": null,
    "term": null,
    "limit": 20
  },
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 800
  }
}
```

### Example 4: Keyword Search Across All Agencies

```json
{
  "federal_register": {
    "agencies": [],
    "document_types": [],
    "start_date": "2025-01-01",
    "term": "artificial intelligence",
    "limit": 30
  },
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 800
  }
}
```

## Customizing AI Output

To change what information is extracted, edit `prompts/analysis_prompt.md`:

### Add New Fields

```markdown
5. **Risk Assessment**: Rate the regulatory impact (Low/Medium/High)
6. **Affected Industries**: List industries impacted by this document

...

{{
  "summary": "...",
  "categories": ["..."],
  "tags": ["..."],
  "key_entities": ["..."],
  "risk_level": "Medium",
  "affected_industries": ["Healthcare", "Technology"]
}}
```

### Change Category Focus

```markdown
2. **Categories**: Up to 5 categories focusing on economic sectors:
   - Primary industry affected
   - Type of regulatory action
   - Economic impact level
```

### Adjust Output Length

In `config.json`:
```json
{
  "ai": {
    "max_tokens": 1200
  }
}
```

In `prompts/analysis_prompt.md`:
```markdown
1. **Executive Summary**: A detailed 4-5 sentence summary including background, key provisions, and expected impact
```

## Best Practices

1. **Start Narrow**: Test with small limits (3-5 documents) before scaling up
2. **Use Specific Agencies**: Filtering by agency significantly improves relevance
3. **Date Ranges**: Recent documents (last 30-60 days) are most useful for monitoring
4. **Temperature**: Keep at 0.2-0.4 for consistent categorization
5. **Prompt Iteration**: Test prompt changes on the same documents to compare results
6. **Token Budget**: Monitor `max_tokens` - increase if summaries are being cut off

## Troubleshooting

**No documents returned:**
- Check agency slugs are correct (use Federal Register website)
- Try broader date range
- Remove document type filters
- Check if your filters are too restrictive

**Inconsistent categorization:**
- Lower temperature (0.1-0.2)
- Provide more specific category examples in prompt
- Use few-shot examples in system prompt

**Summaries too short/long:**
- Adjust `max_tokens` in config
- Modify prompt to request specific length
- Check if abstracts are missing (documents without abstracts have less content)
