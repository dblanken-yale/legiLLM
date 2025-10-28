# AI Data Processor

A flexible two-pass AI processing system for filtering and analyzing arbitrary data.

## Overview

This tool processes data through two AI-powered passes:

1. **Pass 1 (Filter)**: Determines if data is relevant and should be analyzed
2. **Pass 2 (Analysis)**: Analyzes relevant data and generates structured output

## Features

- **Configurable Prompts**: Customize filter and analysis prompts via markdown files
- **Flexible Output Structure**: Define your own output schema
- **Plugin System**: Fetch data from files, databases, APIs, or custom sources
- **Batch Processing**: Process multiple items with rate limiting
- **JSON Output**: Results saved to timestamped JSON files

## Quick Start

### 1. Set Environment Variable

```bash
export PORTKEY_API_KEY='your-api-key-here'
```

### 2. Create Configuration

Copy `config_example.json` to `config.json` and customize:

**Simple file-based config:**
```json
{
  "data_sources": [
    {
      "type": "files",
      "config": {
        "patterns": ["data/*.txt", "docs/**/*.md"]
      }
    }
  ],
  "output_file": "output/processed_data.json"
}
```

**With database:**
```json
{
  "data_sources": [
    {
      "type": "database",
      "config": {
        "db_type": "sqlite",
        "database": "mydata.db",
        "query": "SELECT * FROM content"
      }
    }
  ]
}
```

See [PLUGINS_README.md](PLUGINS_README.md) for full plugin documentation.

### 3. Run the Processor

```bash
python ai_data_processor.py
```

## Configuration

### Environment Variables

- `PORTKEY_API_KEY` (required): Your Portkey API key

### config.json Structure

```json
{
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 800,
    "filter_prompt": null,
    "analysis_prompt": null,
    "system_prompt": null
  },
  "data_sources": [
    {
      "type": "files",
      "config": {
        "patterns": ["data/*.txt", "docs/**/*.md"]
      }
    },
    {
      "type": "database",
      "config": {
        "db_type": "sqlite",
        "database": "data.db",
        "query": "SELECT * FROM items"
      }
    }
  ],
  "input_files": [
    "data/*.txt"
  ],
  "sample_data": [
    "Data item 1"
  ],
  "output_file": "output/results.json",
  "rate_limit_delay": 1.0
}
```

### Data Sources

**Plugin System (Recommended):**

Use `data_sources` to fetch from multiple source types:

```json
{
  "data_sources": [
    {
      "type": "files",
      "config": {"patterns": ["data/*.txt"]}
    },
    {
      "type": "database",
      "config": {
        "db_type": "postgresql",
        "connection": {...},
        "query": "SELECT * FROM content"
      }
    },
    {
      "type": "api",
      "config": {
        "url": "https://api.example.com/data"
      }
    }
  ]
}
```

**See [PLUGINS_README.md](PLUGINS_README.md) for complete plugin documentation.**

### Input Priority

The system checks for data in this order:

1. **`data_sources`** (recommended): Plugin system - files, databases, APIs
2. **`input_files`** (legacy): Glob patterns, auto-converted to files plugin
3. **`sample_data`**: Inline data array
4. **Default**: Built-in sample data

### Loading Files with Glob Patterns

The `input_files` array supports:

**Wildcards:**
- `*.txt` - All .txt files in current directory
- `data/*.md` - All .md files in data/ directory
- `**/*.json` - All .json files recursively

**Multiple patterns:**
```json
"input_files": [
  "data/*.txt",
  "docs/**/*.md",
  "reports/2024-*.json",
  "specific_file.csv"
]
```

**File Format Support:**
- **Text files** (.txt, .md, .csv, etc.): Read as plain text
- **JSON files** (.json): 
  - If JSON contains an array, each item becomes a separate data item
  - If JSON is an object, the entire object is one data item

Each loaded file includes metadata:
```json
{
  "source_file": "/path/to/file.txt",
  "file_type": "txt",
  "content": "file contents..."
}
```

### Custom Prompts

Create markdown files in the `prompts/` directory:

#### prompts/filter_prompt.md

Controls Pass 1 filtering logic. Must return JSON:

```json
{
  "relevant": true,
  "reason": "Explanation of relevance decision"
}
```

#### prompts/analysis_prompt.md

Controls Pass 2 user prompt (what data to analyze). Use `{data}` placeholder for data insertion.

Example:
```markdown
Analyze the following data and extract key insights:

{data}

Focus on identifying the main themes, important entities, and actionable information.
```

#### prompts/system_prompt.md

**This is where you define the output format and structure.** The system prompt instructs the LLM on how to format its response using natural language.

Example for simple categorization:
```markdown
You are a data categorization expert.

Analyze the provided data and respond with ONLY valid JSON in this format:
{
  "category": "primary category",
  "subcategory": "more specific category",
  "confidence": 0.95
}

Provide your best assessment even with limited information.
```

Example for detailed analysis:
```markdown
You are an expert analyst.

Analyze the data and respond with ONLY valid JSON in this format:
{
  "summary": "2-3 sentence overview",
  "sentiment": "positive, negative, or neutral",
  "topics": ["topic1", "topic2", "topic3"],
  "entities": {
    "people": ["person names"],
    "organizations": ["org names"],
    "locations": ["place names"]
  },
  "action_items": ["actionable item 1", "actionable item 2"]
}

Extract all relevant information from the data provided.
```

**Benefits of prompt-based structure:**
- Complete flexibility - define any output format using natural language
- No code changes needed to adjust structure
- Can include detailed instructions, examples, and edge case handling
- LLM interprets and adapts the structure intelligently

## Architecture

The system is split into three modules:

1. **`ai_filter_pass.py`**: First pass - filters data for relevance
2. **`ai_analysis_pass.py`**: Second pass - analyzes and structures data
3. **`ai_data_processor.py`**: Orchestrates both passes and provides pipeline functionality

This modular design allows you to use each pass independently or together.

## Usage as a Library

### Option 1: Use Complete Pipeline (Recommended)

The full pipeline handles both filtering and analysis automatically:

```python
from ai_data_processor import DataProcessingPipeline

# Initialize processor
pipeline = DataProcessingPipeline(
    api_key="your-key",
    output_file="results.json",
    ai_config={
        "model": "gpt-4o-mini",
        "temperature": 0.3
    }
)

# Process data
data_items = [
    "Item 1 to analyze",
    {"title": "Item 2", "content": "..."},
    "Item 3 to analyze"
]

results = pipeline.process_batch(data_items)
```

### Option 2: Use AIDataProcessor for Single Items

Process individual items through both passes:

```python
from ai_data_processor import AIDataProcessor

# Initialize with custom prompts
processor = AIDataProcessor(
    api_key="your-key",
    filter_prompt="Your custom filter prompt...",
    analysis_prompt="Your custom analysis prompt with {data} placeholder",
    system_prompt="""You are an expert analyst.

Respond with ONLY valid JSON in this format:
{
  "custom_field": "description of what you found",
  "another_field": ["array", "of", "items"]
}

Be thorough and accurate."""
)

# Process single item through both passes
result = processor.process_item({"title": "Test", "content": "..."})

if result:
    print(result['analysis'])
```

### Option 3: Use Filter Pass Only

Use just the filtering functionality to determine relevance:

```python
from ai_filter_pass import AIFilterPass

# Initialize filter
filter_pass = AIFilterPass(
    api_key="your-key",
    model="gpt-4o-mini",
    filter_prompt="Your custom filter criteria..."
)

# Filter data items
data_items = [
    "First item to check",
    {"title": "Second item", "content": "..."},
    "Third item to check"
]

for item in data_items:
    is_relevant, reason = filter_pass.filter_data(item)
    if is_relevant:
        print(f"✓ Relevant: {reason}")
        # Do something with relevant item
    else:
        print(f"✗ Filtered: {reason}")
```

### Option 4: Use Analysis Pass Only

Use just the analysis functionality (assumes data is already filtered):

```python
from ai_analysis_pass import AIAnalysisPass

# Initialize analyzer with system prompt defining output format
analysis_pass = AIAnalysisPass(
    api_key="your-key",
    model="gpt-4o-mini",
    analysis_prompt="Analyze this data: {data}",
    system_prompt="""You are an expert analyst.

Respond with ONLY valid JSON:
{
  "summary": "brief summary",
  "key_points": ["point 1", "point 2"],
  "sentiment": "positive, negative, or neutral"
}"""
)

# Analyze pre-filtered data
relevant_items = [
    "Important data item 1",
    {"title": "Critical finding", "details": "..."}
]

for item in relevant_items:
    analysis = analysis_pass.analyze_data(item)
    print(f"Analysis: {analysis}")
```

### Option 5: Mix and Match Passes

Use the passes independently for custom workflows:

```python
from ai_filter_pass import AIFilterPass
from ai_analysis_pass import AIAnalysisPass

# Initialize both passes separately
filter_pass = AIFilterPass(api_key="your-key")
analysis_pass = AIAnalysisPass(
    api_key="your-key",
    system_prompt="""Analyze and respond with JSON:
{"summary": "brief summary", "tags": ["tag1", "tag2"]}"""
)

# Custom processing logic
data_items = ["item1", "item2", "item3"]
filtered_items = []

# First, filter all items
for item in data_items:
    is_relevant, reason = filter_pass.filter_data(item)
    if is_relevant:
        filtered_items.append((item, reason))

print(f"Filtered {len(filtered_items)} from {len(data_items)} items")

# Then analyze filtered items with rate limiting
import time
results = []
for item, filter_reason in filtered_items:
    analysis = analysis_pass.analyze_data(item)
    results.append({
        "item": item,
        "filter_reason": filter_reason,
        "analysis": analysis
    })
    time.sleep(1)  # Rate limiting

# Save results
import json
with open("custom_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Use Case Examples

**Content Moderation (Filter Only):**
```python
from ai_filter_pass import AIFilterPass

filter_pass = AIFilterPass(
    api_key=api_key,
    filter_prompt="Determine if content violates community guidelines..."
)

for post in user_posts:
    violates, reason = filter_pass.filter_data(post)
    if violates:
        flag_for_review(post, reason)
```

**Pre-filtered Analysis (Analysis Only):**
```python
from ai_analysis_pass import AIAnalysisPass

# You already have filtered/relevant data
analysis_pass = AIAnalysisPass(
    api_key=api_key,
    output_structure={"sentiment": "string", "topics": ["array"]}
)

for customer_complaint in high_priority_tickets:
    insights = analysis_pass.analyze_data(customer_complaint)
    route_to_team(insights['topics'])
```

**Custom Two-Stage Pipeline:**
```python
from ai_filter_pass import AIFilterPass
from ai_analysis_pass import AIAnalysisPass

# Stage 1: Quick relevance check with small model
filter_pass = AIFilterPass(api_key=api_key, model="gpt-4o-mini")

relevant_items = [
    item for item in data_items
    if filter_pass.filter_data(item)[0]
]

# Stage 2: Deep analysis with larger model
analysis_pass = AIAnalysisPass(
    api_key=api_key,
    model="gpt-4o",
    max_tokens=2000
)

detailed_results = [
    analysis_pass.analyze_data(item)
    for item in relevant_items
]
```

## Output Format

Results are saved as JSON with the following structure:

```json
[
  {
    "original_data": "The original data item",
    "filter_reason": "Why this was deemed relevant",
    "analysis": {
      "summary": "...",
      "categories": [...],
      "tags": [...],
      "key_points": [...]
    },
    "processed_at": "2025-01-15T10:30:00"
  }
]
```

## Use Cases

### Content Moderation
Filter for policy violations, then categorize and extract details.

### Customer Feedback Analysis
Filter for actionable feedback, then sentiment analysis and categorization.

### Research Paper Processing
Filter for relevance to topic, then extract methodology, findings, and citations.

### News Article Processing
Filter by topic/region, then summarize and extract entities.

### Support Ticket Classification
Filter for technical issues, then categorize by system and priority.

## Advanced Configuration

### Multiple Output Structures

Create different config files for different analysis types:

```bash
python ai_data_processor.py
# Loads config.json by default

# Or load from specific config in your code
```

### Custom Rate Limiting

Adjust `rate_limit_delay` in config.json to control API call frequency:

```json
{
  "rate_limit_delay": 2.0
}
```

### Prompt Engineering Tips

**Filter Prompt:**
- Be specific about relevance criteria
- Include examples of relevant/irrelevant data
- Request brief, actionable reasoning

**Analysis Prompt:**
- Use `{data}` placeholder for data insertion
- Be explicit about output format
- Provide examples of desired output
- Specify constraints (length, format, tone)

## Differences from Federal Register Importer

This is a **generic, reusable** version that:
- Works with any data type (not just Federal Register)
- Has two-pass filtering system
- Supports fully customizable prompts and output structures
- Focuses only on AI processing (no data fetching or Drupal import)
- Outputs only to JSON files

## Troubleshooting

**No results:** Check filter_prompt.md - it may be too strict

**Invalid JSON errors:** Ensure prompts clearly specify JSON-only output

**API errors:** Verify PORTKEY_API_KEY is set correctly

**Missing prompts:** Default prompts will be used if files don't exist

## License

Same as parent project.
