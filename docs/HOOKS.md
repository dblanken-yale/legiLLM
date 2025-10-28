# Hook System Documentation

The hook system provides a flexible, pluggable architecture for data enrichment and processing in the AI analysis pipeline. Hooks allow you to inject custom logic at specific points in the pipeline without modifying core code.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Built-in Hooks](#built-in-hooks)
- [Configuration](#configuration)
- [Creating Custom Hooks](#creating-custom-hooks)
- [Hook Timing Points](#hook-timing-points)
- [Caching](#caching)
- [Examples](#examples)

## Overview

### What are Hooks?

Hooks are pluggable components that can:
- Fetch additional data from external APIs
- Transform or enrich input data before AI analysis
- Post-process AI analysis results
- Add metadata, context, or annotations
- Cache expensive operations automatically

### Why Use Hooks?

- **Separation of concerns**: Keep data source logic separate from analysis logic
- **Reusability**: Write once, use across multiple projects
- **Configurability**: Enable/disable hooks via config, no code changes
- **Maintainability**: Core pipeline remains generic and testable
- **Performance**: Framework-provided caching reduces API calls

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    Analysis Pipeline                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Data Input → HookManager.execute_hooks(pre_analysis)   │
│                      ↓                                    │
│                 AI Analysis                              │
│                      ↓                                    │
│              HookManager.execute_hooks(post_analysis)    │
│                      ↓                                    │
│                 Results Output                            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Key Classes

#### `DataHook` (Abstract Base Class)

Base class for all hooks. Defines the interface that hooks must implement.

```python
class DataHook(ABC):
    @abstractmethod
    def process(self, data: Any, context: Dict) -> Any:
        """Process and potentially enrich data"""
        pass

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        """Generate cache key - return None to disable caching"""
        pass
```

#### `HookManager`

Orchestrates hook execution, manages registration, and provides framework-level caching.

```python
class HookManager:
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize with optional cache directory"""

    def register_hook(self, hook: DataHook, timing: str):
        """Register a hook at specified timing point"""

    def execute_hooks(self, timing: str, data: Any, context: Dict) -> Any:
        """Execute all hooks for a timing point with caching"""
```

## Built-in Hooks

### LegiScan Hook

Fetches full bill text from LegiScan API before AI analysis.

**Features:**
- Fetches complete bill details using `getBill` API operation
- Extracts bill metadata: number, title, description, status, sponsors, subjects
- File-based caching to avoid duplicate API calls
- Graceful error handling (continues with metadata if fetch fails)

**Configuration:**

```json
{
  "hooks": {
    "enabled": true,
    "pre_analysis": [
      {
        "type": "legiscan",
        "description": "Fetch full bill text from LegiScan API"
      }
    ]
  }
}
```

**Environment Variables:**
- `LEGISCAN_API_KEY`: Your LegiScan API key (required)

**Cache Location:**
- `data/cache/legiscan_cache/bill_{bill_id}.json`

## Configuration

### Basic Configuration

Hooks are configured in `config.json`:

```json
{
  "hooks": {
    "enabled": true,
    "cache_directory": "data/cache/hooks",
    "pre_analysis": [
      {
        "type": "hook_type",
        "description": "What this hook does",
        "params": {
          "custom_param": "value"
        }
      }
    ],
    "post_analysis": [
      {
        "type": "another_hook",
        "description": "Post-processing hook"
      }
    ]
  }
}
```

### Configuration Options

- `enabled` (boolean): Master switch for hook system (default: `false`)
- `cache_directory` (string): Path to cache directory (default: `data/cache/hooks`)
- `pre_filter` (array): Hooks to run before filter pass
- `post_filter` (array): Hooks to run after filter pass
- `pre_analysis` (array): Hooks to run before AI analysis
- `post_analysis` (array): Hooks to run after AI analysis

### Hook Configuration Object

Each hook in the timing arrays has:

- `type` (required): Hook type name (must be registered in `HOOK_REGISTRY`)
- `description` (optional): Human-readable description
- `params` (optional): Hook-specific parameters

## Creating Custom Hooks

### Step 1: Create Hook Class

Create a new Python file in `src/hooks/`:

```python
# src/hooks/my_custom_hook.py
from src.hook_system import DataHook
from typing import Any, Dict, Optional

class MyCustomHook(DataHook):
    """
    Description of what your hook does.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize with any required parameters"""
        self.api_key = api_key
        # Add any other initialization

    def process(self, data: Any, context: Dict) -> Any:
        """
        Process and enrich data.

        Args:
            data: Input data (string or dict)
            context: Context dict with item_id and other metadata

        Returns:
            Enriched data (same type as input)
        """
        # Your custom logic here
        item_id = context.get('item_id')

        # Example: Fetch from API
        enriched_data = self._fetch_from_api(item_id)

        # Append to data
        if isinstance(data, str):
            data += f"\n\n## Additional Data:\n\n{enriched_data}"
        elif isinstance(data, dict):
            data['custom_field'] = enriched_data

        return data

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        """
        Generate cache key for this hook.

        Return None to disable caching for this hook.
        """
        item_id = context.get('item_id')
        if item_id:
            return f"my_custom_hook_{item_id}"
        return None

    def _fetch_from_api(self, item_id: str) -> str:
        """Your custom API fetch logic"""
        # Implementation here
        pass
```

### Step 2: Register Hook

Add your hook to `src/hook_registry.py`:

```python
from src.hooks.my_custom_hook import MyCustomHook

HOOK_REGISTRY: Dict[str, type[DataHook]] = {
    'legiscan': LegiScanHook,
    'my_custom': MyCustomHook,  # Add your hook
}
```

Update the `create_hook_from_config` function if your hook needs special initialization:

```python
def create_hook_from_config(hook_config: Dict[str, Any], default_cache_dir: Optional[Path] = None) -> Optional[DataHook]:
    hook_type = hook_config.get('type')
    hook_params = hook_config.get('params', {})

    if hook_type == 'my_custom':
        api_key = hook_params.get('api_key') or os.getenv('MY_API_KEY')
        return MyCustomHook(api_key=api_key)

    # ... existing code ...
```

### Step 3: Configure Hook

Add to your `config.json`:

```json
{
  "hooks": {
    "enabled": true,
    "pre_analysis": [
      {
        "type": "my_custom",
        "description": "Fetch additional data from custom API",
        "params": {
          "custom_setting": "value"
        }
      }
    ]
  }
}
```

### Step 4: Use in Pipeline

The hook will automatically execute when you run the analysis pass:

```bash
python scripts/run_analysis_pass.py
```

## Hook Timing Points

Hooks can execute at different points in the pipeline:

### `pre_filter`
- Runs before the filter pass
- Use for: Enriching raw data before filtering

### `post_filter`
- Runs after the filter pass
- Use for: Processing filter results before analysis

### `pre_analysis`
- Runs before AI analysis
- Use for: Fetching full text, adding context
- **Most common timing point**

### `post_analysis`
- Runs after AI analysis
- Use for: Enriching AI results, adding metadata

## Caching

### Framework-Provided Caching

The `HookManager` provides automatic caching for all hooks:

1. **Generate cache key**: Hook implements `get_cache_key()`
2. **Check cache**: HookManager checks if result exists
3. **Execute or load**: Run hook or load cached result
4. **Save to cache**: Cache successful results

### Cache Key Generation

```python
def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
    """
    Generate unique cache key for this data.

    - Use item_id from context for per-item caching
    - Return None to disable caching
    - Must be unique across all invocations
    """
    item_id = context.get('item_id')
    if item_id:
        return f"{self.__class__.__name__}_{item_id}"
    return None
```

### Cache Location

- Framework cache: `data/cache/hooks/{cache_key}.json`
- Hook-specific cache: Custom (e.g., LegiScan uses `data/cache/legiscan_cache/`)

### Disabling Cache

To disable caching for a hook, return `None` from `get_cache_key()`:

```python
def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
    return None  # Cache disabled
```

## Examples

### Example 1: Basic Enrichment Hook

```python
from src.hook_system import DataHook

class MetadataHook(DataHook):
    """Add metadata to all items"""

    def process(self, data: Any, context: Dict) -> Any:
        import datetime

        metadata = f"\n\nProcessed at: {datetime.datetime.now()}"

        if isinstance(data, str):
            return data + metadata
        elif isinstance(data, dict):
            data['processed_at'] = datetime.datetime.now().isoformat()

        return data

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        return None  # Don't cache timestamps
```

### Example 2: API Enrichment Hook

```python
from src.hook_system import DataHook
import requests

class ExternalAPIHook(DataHook):
    """Fetch additional data from external API"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def process(self, data: Any, context: Dict) -> Any:
        item_id = context.get('item_id')
        if not item_id:
            return data

        # Fetch from API
        response = requests.get(
            f"{self.base_url}/items/{item_id}",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )

        if response.ok:
            api_data = response.json()

            if isinstance(data, str):
                data += f"\n\n## API Data:\n\n{api_data}"
            elif isinstance(data, dict):
                data['api_enrichment'] = api_data

        return data

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        item_id = context.get('item_id')
        return f"external_api_{item_id}" if item_id else None
```

### Example 3: Post-Analysis Hook

```python
from src.hook_system import DataHook

class CategorizationHook(DataHook):
    """Add additional categorization after AI analysis"""

    def process(self, data: Any, context: Dict) -> Any:
        """
        For post-analysis hooks, data is the AI analysis result dict
        """
        if not isinstance(data, dict):
            return data

        # Add custom categorization
        categories = data.get('categories', [])

        if 'Pediatric' in ' '.join(categories):
            if 'pediatric_specialist' not in data:
                data['pediatric_specialist'] = True
                data['requires_review'] = True

        return data

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        # Cache using original item_id
        item_id = context.get('item_id')
        return f"categorization_{item_id}" if item_id else None
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully and return original data:

```python
def process(self, data: Any, context: Dict) -> Any:
    try:
        # Your logic here
        return enriched_data
    except Exception as e:
        logger.warning(f"Hook failed: {e}")
        return data  # Return original data on error
```

### 2. Logging

Use logging to track hook execution:

```python
import logging
logger = logging.getLogger(__name__)

def process(self, data: Any, context: Dict) -> Any:
    item_id = context.get('item_id')
    logger.info(f"Processing item {item_id}")
    # ... logic ...
    logger.info(f"Successfully enriched item {item_id}")
    return data
```

### 3. Type Flexibility

Support both string and dict data types:

```python
def process(self, data: Any, context: Dict) -> Any:
    enrichment = self._get_enrichment()

    if isinstance(data, str):
        return data + f"\n\n{enrichment}"
    elif isinstance(data, dict):
        data['enrichment'] = enrichment

    return data
```

### 4. Cache Key Uniqueness

Ensure cache keys are globally unique:

```python
def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
    item_id = context.get('item_id')
    # Include hook class name for uniqueness
    return f"{self.__class__.__name__}_{item_id}"
```

## Troubleshooting

### Hook Not Executing

1. Check `hooks.enabled` is `true` in config
2. Verify hook is registered in `HOOK_REGISTRY`
3. Check hook type name matches config
4. Check logs for registration messages

### Cache Not Working

1. Verify `cache_directory` exists and is writable
2. Check `get_cache_key()` returns non-None value
3. Look for cache files in `data/cache/hooks/`
4. Check logs for cache-related errors

### Hook Errors

1. Check logs for error messages
2. Verify API keys are set in environment
3. Test hook independently with sample data
4. Add debug logging to hook methods

## Migration from Hardcoded Logic

To migrate existing hardcoded data fetching to hooks:

1. **Extract logic**: Copy fetch/enrichment code to new hook class
2. **Add to registry**: Register in `src/hook_registry.py`
3. **Update config**: Add hook to appropriate timing point
4. **Remove old code**: Delete hardcoded logic from pipeline
5. **Test**: Verify behavior is identical with hook enabled

See the LegiScan refactor as an example:
- Before: `ai_analysis_pass.py` lines 211-368 (hardcoded)
- After: `src/hooks/legiscan_hook.py` (pluggable hook)

## Future Enhancements

Potential improvements to the hook system:

- **Async hooks**: Support for `async def process()`
- **Hook dependencies**: Specify execution order dependencies
- **Conditional execution**: Skip hooks based on data attributes
- **Hook composition**: Chain multiple hooks together
- **Monitoring**: Track hook performance and success rates
- **Remote hooks**: Execute hooks via HTTP API

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall system architecture
- [CONFIGURATION.md](CONFIGURATION.md) - Complete configuration reference
- [PLUGINS.md](PLUGINS.md) - Data source plugins (for data ingestion)

---

**Note**: Hooks are for data enrichment/processing. For data *ingestion* (fetching raw data), use data source plugins instead (see [PLUGINS.md](PLUGINS.md)).
