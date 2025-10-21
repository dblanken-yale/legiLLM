# Analysis Task Prompt

Analyze this Federal Register document and provide:

1. **Executive Summary**: A concise 2-3 sentence summary of the document's key points and implications
2. **Categories**: Up to 5 relevant high-level categories (e.g., Healthcare, Environment, Finance, Labor, Technology, Transportation, Energy, Agriculture)
3. **Tags**: Up to 10 specific tags/keywords that describe the content, topics, or entities involved
4. **Key Entities**: Important agencies, organizations, locations, or individuals mentioned

## Document Information

**Title**: {title}
{doc_type_label}**Content**: {content}

## Response Format

Respond ONLY with valid JSON in this exact format:
```json
{{
  "summary": "Your 2-3 sentence executive summary here",
  "categories": ["Category1", "Category2", "Category3"],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "key_entities": ["Entity 1", "Entity 2", "Entity 3"]
}}
```

Do not include any text before or after the JSON.
