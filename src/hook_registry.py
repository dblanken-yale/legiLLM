"""
Hook Registry for Data Enrichment Hooks

Maps hook type names to hook classes for dynamic instantiation from config.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from src.hook_system import DataHook
from src.hooks.legiscan_hook import LegiScanHook

logger = logging.getLogger(__name__)

# Registry mapping hook type names to hook classes
HOOK_REGISTRY: Dict[str, type[DataHook]] = {
    'legiscan': LegiScanHook,
}


def create_hook_from_config(
    hook_config: Dict[str, Any],
    default_cache_dir: Optional[Path] = None
) -> Optional[DataHook]:
    """
    Create a hook instance from configuration.

    Args:
        hook_config: Hook configuration dict with 'type' and optional parameters
        default_cache_dir: Default cache directory if not specified in config

    Returns:
        Instantiated hook or None if type not found

    Example:
        hook_config = {
            'type': 'legiscan',
            'description': 'Fetch full bill text from LegiScan API'
        }
        hook = create_hook_from_config(hook_config)
    """
    hook_type = hook_config.get('type')
    if not hook_type:
        logger.warning(f"Hook config missing 'type': {hook_config}")
        return None

    hook_class = HOOK_REGISTRY.get(hook_type)
    if not hook_class:
        logger.warning(f"Unknown hook type: {hook_type}")
        logger.warning(f"Available hook types: {list(HOOK_REGISTRY.keys())}")
        return None

    # Get hook-specific parameters
    hook_params = hook_config.get('params', {})

    # Handle hook-specific initialization
    if hook_type == 'legiscan':
        # LegiScan hook needs API key and cache directory
        api_key = hook_params.get('api_key') or os.getenv('LEGISCAN_API_KEY')
        cache_dir = hook_params.get('cache_dir')
        if cache_dir:
            cache_dir = Path(cache_dir)

        return hook_class(api_key=api_key, cache_dir=cache_dir)

    # Generic hook initialization (for future hooks)
    try:
        return hook_class(**hook_params)
    except TypeError as e:
        logger.error(f"Error initializing hook {hook_type}: {e}")
        return None


def register_hooks_from_config(
    hook_manager,
    config: Dict[str, Any],
    default_cache_dir: Optional[Path] = None
):
    """
    Register hooks from configuration into hook manager.

    Args:
        hook_manager: HookManager instance
        config: Configuration dict with hooks section
        default_cache_dir: Default cache directory for hooks

    Example config:
        {
            "hooks": {
                "enabled": true,
                "cache_directory": "data/cache/hooks",
                "pre_analysis": [
                    {
                        "type": "legiscan",
                        "description": "Fetch full bill text from LegiScan API"
                    }
                ],
                "post_analysis": [
                    {
                        "type": "custom_enrichment",
                        "params": {"key": "value"}
                    }
                ]
            }
        }
    """
    hooks_config = config.get('hooks', {})

    if not hooks_config.get('enabled', False):
        logger.info("Hooks are disabled in config")
        return

    # Register hooks for each timing point
    for timing in ['pre_filter', 'post_filter', 'pre_analysis', 'post_analysis']:
        timing_hooks = hooks_config.get(timing, [])

        for hook_config in timing_hooks:
            hook = create_hook_from_config(hook_config, default_cache_dir)

            if hook:
                hook_manager.register_hook(hook, timing)
                hook_type = hook_config.get('type')
                description = hook_config.get('description', '')
                logger.info(f"Registered {hook_type} hook at {timing}: {description}")
            else:
                logger.warning(f"Failed to create hook from config: {hook_config}")
