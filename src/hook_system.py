"""
Hook System for Data Enrichment Pipeline

Provides a flexible hook system that allows custom data processing
before and after AI analysis. Hooks can fetch additional data,
transform inputs, or enrich outputs.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class HookTiming:
    """Constants for hook execution timing"""
    PRE_FILTER = "pre_filter"
    POST_FILTER = "post_filter"
    PRE_ANALYSIS = "pre_analysis"
    POST_ANALYSIS = "post_analysis"


class DataHook(ABC):
    """
    Base class for data enrichment hooks.

    Hooks can fetch additional data, transform inputs, or enrich outputs
    at various points in the pipeline.
    """

    @abstractmethod
    def process(self, data: Any, context: Dict) -> Any:
        """
        Process and potentially enrich data.

        Args:
            data: Input data (document, bill, etc.)
            context: Additional context (item_id, config, etc.)

        Returns:
            Processed/enriched data
        """
        pass

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        """
        Generate cache key for this data.

        Return None to disable caching for this hook.
        Default implementation uses item_id from context.

        Args:
            data: Input data
            context: Context dictionary

        Returns:
            Cache key string or None to disable caching
        """
        if 'item_id' in context:
            return f"{self.__class__.__name__}_{context['item_id']}"
        return None


class HookManager:
    """
    Manages and executes hooks with framework-provided caching.

    Hooks can be registered for different timing points in the pipeline.
    The manager handles execution order, caching, and error handling.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize hook manager.

        Args:
            cache_dir: Optional cache directory for hook results
        """
        self.hooks: Dict[str, list] = {}
        self.cache_dir = cache_dir

        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Hook cache directory: {cache_dir}")

    def register_hook(
        self,
        hook: DataHook,
        timing: str
    ):
        """
        Register a hook to run at specified timing.

        Args:
            hook: DataHook instance to register
            timing: When to run (use HookTiming constants)
        """
        if timing not in self.hooks:
            self.hooks[timing] = []

        self.hooks[timing].append(hook)
        logger.debug(f"Registered hook {hook.__class__.__name__} at {timing}")

    def execute_hooks(
        self,
        timing: str,
        data: Any,
        context: Dict
    ) -> Any:
        """
        Execute all hooks for a timing point, with caching.

        Args:
            timing: Timing point (use HookTiming constants)
            data: Input data
            context: Context dictionary

        Returns:
            Data after all hooks have processed it
        """
        if timing not in self.hooks:
            return data

        result = data

        for hook in self.hooks[timing]:
            try:
                # Check cache
                cache_key = hook.get_cache_key(result, context)
                cached = self._load_from_cache(cache_key) if cache_key else None

                if cached is not None:
                    logger.debug(f"Using cached result for {hook.__class__.__name__}")
                    result = cached
                else:
                    # Execute hook
                    result = hook.process(result, context)

                    # Save to cache
                    if cache_key:
                        self._save_to_cache(cache_key, result)

            except Exception as e:
                logger.warning(f"Hook {hook.__class__.__name__} failed: {e}")
                # Continue with unmodified data on error

        return result

    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Load from framework cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if not found
        """
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Cache load failed for {cache_key}: {e}")

        return None

    def _save_to_cache(self, cache_key: str, data: Any):
        """
        Save to framework cache.

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                # Only cache string data or simple dicts
                if isinstance(data, (str, dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Cache save failed for {cache_key}: {e}")
