#!/usr/bin/env python3
"""
Data Source Plugin System for AI Data Processor
Provides extensible plugin architecture for fetching data from various sources.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from glob import glob
import json
import logging

logger = logging.getLogger(__name__)


class DataSourcePlugin(ABC):
    """
    Abstract base class for data source plugins.
    
    All plugins must implement the fetch_data() method which returns
    a list of data items to be processed by the AI.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self):
        """
        Validate plugin configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def fetch_data(self) -> List[Any]:
        """
        Fetch data from source.
        
        Returns:
            List of data items to process
        """
        pass
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Get human-readable plugin name.
        
        Returns:
            Plugin name string
        """
        pass


class FilesPlugin(DataSourcePlugin):
    """
    Plugin for loading data from files using glob patterns.
    
    Config:
        patterns: List of file path patterns
        recursive: Enable recursive glob (default: True)
    """
    
    def get_plugin_name(self) -> str:
        return "Files Plugin"
    
    def validate_config(self):
        if 'patterns' not in self.config:
            raise ValueError("FilesPlugin requires 'patterns' in config")
        
        if not isinstance(self.config['patterns'], list):
            raise ValueError("FilesPlugin 'patterns' must be a list")
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Load files matching patterns.
        
        Returns:
            List of dictionaries with file metadata and content
        """
        patterns = self.config['patterns']
        recursive = self.config.get('recursive', True)
        data_items = []
        
        logger.info(f"{self.get_plugin_name()}: Processing {len(patterns)} pattern(s)")
        
        for pattern in patterns:
            matched_files = glob(pattern, recursive=recursive)
            
            if not matched_files:
                logger.warning(f"No files matched pattern: {pattern}")
                continue
            
            logger.info(f"Pattern '{pattern}' matched {len(matched_files)} file(s)")
            
            for file_path in matched_files:
                try:
                    file_path_obj = Path(file_path)
                    
                    if not file_path_obj.is_file():
                        continue
                    
                    suffix = file_path_obj.suffix.lower()
                    
                    if suffix == '.json':
                        with open(file_path_obj, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            
                            if isinstance(content, list):
                                for idx, item in enumerate(content):
                                    data_items.append({
                                        'source_file': str(file_path_obj),
                                        'file_type': 'json',
                                        'array_index': idx,
                                        'content': item
                                    })
                            else:
                                data_items.append({
                                    'source_file': str(file_path_obj),
                                    'file_type': 'json',
                                    'content': content
                                })
                    else:
                        with open(file_path_obj, 'r', encoding='utf-8') as f:
                            content = f.read()
                            data_items.append({
                                'source_file': str(file_path_obj),
                                'file_type': suffix[1:] if suffix else 'txt',
                                'content': content
                            })
                    
                    logger.debug(f"Loaded: {file_path_obj}")
                    
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
        
        logger.info(f"{self.get_plugin_name()}: Loaded {len(data_items)} data item(s)")
        return data_items


class DatabasePlugin(DataSourcePlugin):
    """
    Plugin for loading data from databases.
    
    Supports: PostgreSQL, MySQL, SQLite
    
    Config:
        db_type: 'postgresql', 'mysql', or 'sqlite'
        connection: Connection parameters (varies by db_type)
        query: SQL query to execute
        params: Optional query parameters
    """
    
    def get_plugin_name(self) -> str:
        return "Database Plugin"
    
    def validate_config(self):
        required = ['db_type', 'query']
        for field in required:
            if field not in self.config:
                raise ValueError(f"DatabasePlugin requires '{field}' in config")
        
        db_type = self.config['db_type'].lower()
        if db_type not in ['postgresql', 'mysql', 'sqlite']:
            raise ValueError(f"Unsupported db_type: {db_type}")
        
        if db_type in ['postgresql', 'mysql'] and 'connection' not in self.config:
            raise ValueError(f"DatabasePlugin requires 'connection' config for {db_type}")
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Execute query and return results.
        
        Returns:
            List of dictionaries (one per row)
        """
        db_type = self.config['db_type'].lower()
        query = self.config['query']
        params = self.config.get('params', [])
        
        logger.info(f"{self.get_plugin_name()}: Connecting to {db_type}")
        
        if db_type == 'sqlite':
            return self._fetch_sqlite(query, params)
        elif db_type == 'postgresql':
            return self._fetch_postgresql(query, params)
        elif db_type == 'mysql':
            return self._fetch_mysql(query, params)
    
    def _fetch_sqlite(self, query: str, params: List) -> List[Dict[str, Any]]:
        """Fetch data from SQLite database."""
        try:
            import sqlite3
        except ImportError:
            raise ImportError("sqlite3 not available")
        
        db_path = self.config.get('connection', {}).get('database', self.config.get('database'))
        
        if not db_path:
            raise ValueError("SQLite requires 'database' path in connection config")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data_items = [dict(row) for row in rows]
            
            conn.close()
            
            logger.info(f"{self.get_plugin_name()}: Fetched {len(data_items)} row(s)")
            return data_items
            
        except Exception as e:
            logger.error(f"SQLite error: {e}")
            raise
    
    def _fetch_postgresql(self, query: str, params: List) -> List[Dict[str, Any]]:
        """Fetch data from PostgreSQL database."""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
        
        connection_config = self.config['connection']
        
        try:
            conn = psycopg2.connect(**connection_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data_items = [dict(row) for row in rows]
            
            cursor.close()
            conn.close()
            
            logger.info(f"{self.get_plugin_name()}: Fetched {len(data_items)} row(s)")
            return data_items
            
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            raise
    
    def _fetch_mysql(self, query: str, params: List) -> List[Dict[str, Any]]:
        """Fetch data from MySQL database."""
        try:
            import mysql.connector
        except ImportError:
            raise ImportError("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
        
        connection_config = self.config['connection']
        
        try:
            conn = mysql.connector.connect(**connection_config)
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data_items = list(rows)
            
            cursor.close()
            conn.close()
            
            logger.info(f"{self.get_plugin_name()}: Fetched {len(data_items)} row(s)")
            return data_items
            
        except Exception as e:
            logger.error(f"MySQL error: {e}")
            raise


class APIPlugin(DataSourcePlugin):
    """
    Plugin for loading data from REST APIs.
    
    Config:
        url: API endpoint URL
        method: HTTP method (default: GET)
        headers: Optional request headers
        params: Optional query parameters
        json_path: Optional JSONPath to extract data from response
    """
    
    def get_plugin_name(self) -> str:
        return "API Plugin"
    
    def validate_config(self):
        if 'url' not in self.config:
            raise ValueError("APIPlugin requires 'url' in config")
    
    def fetch_data(self) -> List[Any]:
        """
        Fetch data from API endpoint.
        
        Returns:
            List of data items from API response
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests not installed. Install with: pip install requests")
        
        url = self.config['url']
        method = self.config.get('method', 'GET').upper()
        headers = self.config.get('headers', {})
        params = self.config.get('params', {})
        json_body = self.config.get('json')
        
        logger.info(f"{self.get_plugin_name()}: Fetching from {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, json=json_body)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            json_path = self.config.get('json_path')
            if json_path:
                data = self._extract_json_path(data, json_path)
            
            if isinstance(data, list):
                logger.info(f"{self.get_plugin_name()}: Fetched {len(data)} item(s)")
                return data
            else:
                logger.info(f"{self.get_plugin_name()}: Fetched 1 item")
                return [data]
                
        except Exception as e:
            logger.error(f"API error: {e}")
            raise
    
    def _extract_json_path(self, data: Any, path: str) -> Any:
        """
        Extract data using simple dot notation path.
        
        Args:
            data: JSON data
            path: Dot-separated path (e.g., 'results.items')
            
        Returns:
            Extracted data
        """
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                raise ValueError(f"Cannot traverse path '{path}' in data")
        
        return current


class PluginManager:
    """
    Manages data source plugins and loads data from configured sources.
    """
    
    PLUGIN_TYPES = {
        'files': FilesPlugin,
        'database': DatabasePlugin,
        'api': APIPlugin
    }
    
    def __init__(self, plugins_config: List[Dict[str, Any]]):
        """
        Initialize plugin manager.
        
        Args:
            plugins_config: List of plugin configurations
        """
        self.plugins_config = plugins_config
        self.plugins = []
        self._initialize_plugins()
    
    def _initialize_plugins(self):
        """Initialize all configured plugins."""
        for plugin_config in self.plugins_config:
            plugin_type = plugin_config.get('type')
            
            if not plugin_type:
                logger.warning("Plugin config missing 'type', skipping")
                continue
            
            plugin_class = self.PLUGIN_TYPES.get(plugin_type.lower())
            
            if not plugin_class:
                logger.warning(f"Unknown plugin type: {plugin_type}")
                continue
            
            try:
                plugin = plugin_class(plugin_config.get('config', {}))
                self.plugins.append(plugin)
                logger.info(f"Initialized {plugin.get_plugin_name()}")
            except Exception as e:
                logger.error(f"Failed to initialize {plugin_type} plugin: {e}")
    
    def fetch_all_data(self) -> List[Any]:
        """
        Fetch data from all configured plugins.
        
        Returns:
            Combined list of data items from all plugins
        """
        all_data = []
        
        for plugin in self.plugins:
            try:
                data = plugin.fetch_data()
                all_data.extend(data)
            except Exception as e:
                logger.error(f"Error fetching data from {plugin.get_plugin_name()}: {e}")
        
        logger.info(f"Total data items from all plugins: {len(all_data)}")
        return all_data
    
    @classmethod
    def register_plugin(cls, name: str, plugin_class: type):
        """
        Register a custom plugin type.
        
        Args:
            name: Plugin type name
            plugin_class: Plugin class (must extend DataSourcePlugin)
        """
        if not issubclass(plugin_class, DataSourcePlugin):
            raise ValueError("Plugin class must extend DataSourcePlugin")
        
        cls.PLUGIN_TYPES[name.lower()] = plugin_class
        logger.info(f"Registered custom plugin: {name}")
