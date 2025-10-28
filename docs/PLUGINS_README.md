# Data Source Plugin System

Extensible plugin architecture for fetching data from multiple sources.

## Overview

The plugin system allows you to fetch data from:
- **Files** (with glob patterns)
- **Databases** (PostgreSQL, MySQL, SQLite)
- **APIs** (REST endpoints)
- **Custom** (create your own plugins)

## Quick Start

### Using Plugins in config.json

```json
{
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
        "database": "mydata.db",
        "query": "SELECT * FROM articles"
      }
    }
  ]
}
```

## Built-in Plugins

### Files Plugin

Load data from files using glob patterns.

**Config:**
```json
{
  "type": "files",
  "config": {
    "patterns": [
      "data/*.txt",
      "data/*.md",
      "data/subfolder/**/*.json"
    ],
    "recursive": true
  }
}
```

**Features:**
- Glob pattern support (`*`, `**`)
- JSON arrays automatically split into items
- Includes file metadata (source_file, file_type)

### Database Plugin

Query relational databases.

**Supported Databases:**
- SQLite (built-in Python support)
- PostgreSQL (requires `psycopg2-binary`)
- MySQL (requires `mysql-connector-python`)

#### SQLite Example

```json
{
  "type": "database",
  "config": {
    "db_type": "sqlite",
    "database": "data/mydata.db",
    "query": "SELECT id, title, content FROM articles WHERE published = 1",
    "params": []
  }
}
```

#### PostgreSQL Example

```json
{
  "type": "database",
  "config": {
    "db_type": "postgresql",
    "connection": {
      "host": "localhost",
      "port": 5432,
      "database": "myapp",
      "user": "postgres",
      "password": "password"
    },
    "query": "SELECT * FROM posts WHERE status = %s LIMIT 100",
    "params": ["published"]
  }
}
```

#### MySQL Example

```json
{
  "type": "database",
  "config": {
    "db_type": "mysql",
    "connection": {
      "host": "localhost",
      "user": "root",
      "password": "password",
      "database": "myapp"
    },
    "query": "SELECT * FROM posts WHERE status = %s LIMIT 100",
    "params": ["published"]
  }
}
```

#### MariaDB / LegiScan Database Example

MariaDB uses the MySQL protocol, so use `"db_type": "mysql"` for MariaDB databases.

**Docker Host Network Mode:**
```json
{
  "type": "database",
  "config": {
    "db_type": "mysql",
    "connection": {
      "host": "localhost",
      "port": 3306,
      "database": "legiscan",
      "user": "your_username",
      "password": "your_password"
    },
    "query": "SELECT bill_id, bill_number, title, description, status, state_id FROM ls_bill ORDER BY status_date DESC LIMIT 100",
    "params": []
  }
}
```

**Common LegiScan Query Patterns:**

All bills:
```sql
SELECT * FROM ls_bill
```

Bills by state (requires state_id):
```sql
SELECT * FROM ls_bill WHERE state_id = %s ORDER BY status_date DESC
```

Recent bills (last 30 days):
```sql
SELECT * FROM ls_bill WHERE status_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
```

Bills by status:
```sql
SELECT * FROM ls_bill WHERE status = %s ORDER BY status_date DESC
```

Custom field selection (to reduce API costs):
```sql
SELECT bill_id, title, description, status FROM ls_bill WHERE state_id = %s
```

**Docker Network Notes:**
- **Host network mode**: Use `localhost:3306`
- **Bridge with port mapping** (e.g., 3307:3306): Use `localhost:3307`
- **Custom Docker network**: Use container name as host

See `config_legiscan_example.json` for complete example.

**Install database drivers:**
```bash
# PostgreSQL
pip install psycopg2-binary

# MySQL / MariaDB
pip install mysql-connector-python
```

### API Plugin

Fetch data from REST APIs.

**Config:**
```json
{
  "type": "api",
  "config": {
    "url": "https://api.example.com/data",
    "method": "GET",
    "headers": {
      "Authorization": "Bearer YOUR_TOKEN",
      "Content-Type": "application/json"
    },
    "params": {
      "limit": 100,
      "filter": "active"
    },
    "json_path": "results.items"
  }
}
```

**Options:**
- `url` (required): API endpoint
- `method`: HTTP method (GET or POST)
- `headers`: Request headers
- `params`: Query parameters
- `json`: Request body for POST
- `json_path`: Dot notation to extract data from response (e.g., `"data.results"`)

**Example with POST:**
```json
{
  "type": "api",
  "config": {
    "url": "https://api.example.com/search",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer TOKEN"
    },
    "json": {
      "query": "test",
      "limit": 50
    },
    "json_path": "data"
  }
}
```

## Multiple Data Sources

Combine multiple plugins to fetch from different sources:

```json
{
  "data_sources": [
    {
      "type": "files",
      "config": {
        "patterns": ["documents/*.txt"]
      }
    },
    {
      "type": "database",
      "config": {
        "db_type": "sqlite",
        "database": "app.db",
        "query": "SELECT * FROM content"
      }
    },
    {
      "type": "api",
      "config": {
        "url": "https://api.example.com/items",
        "method": "GET"
      }
    }
  ]
}
```

All data is combined and processed together.

## Creating Custom Plugins

Extend `DataSourcePlugin` to create custom data sources.

### Example: RSS Feed Plugin

```python
from data_source_plugins import DataSourcePlugin
import feedparser

class RSSPlugin(DataSourcePlugin):
    def get_plugin_name(self) -> str:
        return "RSS Plugin"
    
    def validate_config(self):
        if 'feed_url' not in self.config:
            raise ValueError("RSSPlugin requires 'feed_url'")
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        feed_url = self.config['feed_url']
        feed = feedparser.parse(feed_url)
        
        items = []
        for entry in feed.entries:
            items.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary,
                'published': entry.published
            })
        
        return items

# Register the plugin
from data_source_plugins import PluginManager
PluginManager.register_plugin('rss', RSSPlugin)
```

### Use Custom Plugin

```json
{
  "data_sources": [
    {
      "type": "rss",
      "config": {
        "feed_url": "https://example.com/feed.xml"
      }
    }
  ]
}
```

## Configuration Priority

The system checks for data sources in this order:

1. **`data_sources`** (plugin system) - Recommended
2. **`input_files`** (legacy) - Converted to files plugin automatically
3. **`sample_data`** (inline data)
4. **Default samples** (fallback)

## Example Configs

See example configuration files:
- `config_plugins_example.json` - Multiple plugins
- `config_database_example.json` - Database-focused (PostgreSQL)
- `config_legiscan_example.json` - LegiScan MariaDB database
- `config_example.json` - Legacy input_files format (still supported)

## Use Cases

### Legislative Bill Analysis
```json
{
  "data_sources": [
    {
      "type": "database",
      "config": {
        "db_type": "mysql",
        "connection": {
          "host": "localhost",
          "port": 3306,
          "database": "legiscan",
          "user": "legiscan_user",
          "password": "password"
        },
        "query": "SELECT bill_id, title, description, status FROM ls_bill WHERE state_id = %s AND status_date >= DATE_SUB(NOW(), INTERVAL 90 DAY)",
        "params": [42]
      }
    }
  ]
}
```

### Content Management
```json
{
  "data_sources": [
    {
      "type": "database",
      "config": {
        "db_type": "postgresql",
        "connection": {...},
        "query": "SELECT title, body FROM articles WHERE needs_review = true"
      }
    }
  ]
}
```

### Document Processing
```json
{
  "data_sources": [
    {
      "type": "files",
      "config": {
        "patterns": ["inbox/**/*.pdf", "inbox/**/*.docx"]
      }
    }
  ]
}
```

### Social Media Monitoring
```json
{
  "data_sources": [
    {
      "type": "api",
      "config": {
        "url": "https://api.twitter.com/2/tweets/search/recent",
        "headers": {"Authorization": "Bearer TOKEN"},
        "params": {"query": "brand mentions"},
        "json_path": "data"
      }
    }
  ]
}
```

### Multi-Source Research
```json
{
  "data_sources": [
    {
      "type": "files",
      "config": {"patterns": ["research/*.txt"]}
    },
    {
      "type": "database",
      "config": {
        "db_type": "sqlite",
        "database": "research.db",
        "query": "SELECT * FROM papers"
      }
    },
    {
      "type": "api",
      "config": {
        "url": "https://api.arxiv.org/search",
        "params": {"query": "machine learning"}
      }
    }
  ]
}
```

## Error Handling

Plugins fail gracefully:
- Invalid plugin type: Warning logged, skipped
- Plugin initialization error: Error logged, skipped
- Plugin fetch error: Error logged, other plugins continue
- Missing dependencies: Clear error message with install instructions

## Plugin Development Guidelines

When creating custom plugins:

1. **Extend DataSourcePlugin**
2. **Implement required methods:**
   - `get_plugin_name()` - Return plugin name
   - `validate_config()` - Validate config, raise ValueError if invalid
   - `fetch_data()` - Return List[Any] of data items
3. **Handle errors gracefully**
4. **Log important events**
5. **Register with PluginManager.register_plugin()**

## Troubleshooting

**Plugin not loading:**
- Check plugin type name matches registered name
- Verify config structure matches plugin requirements

**Database connection fails:**
- Verify database driver is installed
- Check connection parameters
- Test query separately

**API errors:**
- Check API endpoint and credentials
- Verify json_path if used
- Check rate limits

**No data returned:**
- Check plugin logs for errors
- Verify data source contains data
- Test queries/patterns separately
