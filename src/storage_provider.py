"""
Storage Provider Abstract Base Class

Defines the interface for storage backends (local files, Azure Blob, PostgreSQL, etc.)
Allows the application to run identically in local and Azure environments.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union


class StorageProvider(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def save_raw_data(self, filename: str, data: Dict[str, Any]) -> None:
        """
        Save raw bill data from LegiScan API

        Args:
            filename: Name/identifier for the data (e.g., "ct_bills_2025")
            data: Dictionary containing bill data
        """
        pass

    @abstractmethod
    def load_raw_data(self, filename: str) -> Dict[str, Any]:
        """
        Load raw bill data

        Args:
            filename: Name/identifier for the data (e.g., "ct_bills_2025")

        Returns:
            Dictionary containing bill data

        Raises:
            FileNotFoundError: If data doesn't exist
        """
        pass

    @abstractmethod
    def save_filtered_results(self, run_id: str, data: Dict[str, Any]) -> None:
        """
        Save filter pass results

        Args:
            run_id: Unique identifier for this filter run (e.g., "ct_bills_2025")
            data: Dictionary containing filter results with structure:
                {
                    "summary": {...},
                    "relevant_bills": [...]
                }
        """
        pass

    @abstractmethod
    def load_filtered_results(self, run_id: str) -> Dict[str, Any]:
        """
        Load filter pass results

        Args:
            run_id: Unique identifier for the filter run

        Returns:
            Dictionary containing filter results

        Raises:
            FileNotFoundError: If results don't exist
        """
        pass

    @abstractmethod
    def save_analysis_results(
        self,
        run_id: str,
        relevant: Union[List[Dict[str, Any]], Dict[str, Any]],
        not_relevant: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Save analysis pass results

        Supports two formats for backward compatibility:

        Format 1 (legacy): List of results
            relevant: [{"bill": {...}, "analysis": {...}}, ...]
            not_relevant: [{"bill": {...}, "analysis": {...}}, ...]

        Format 2 (with stats): Dict containing summary, timing stats, and results
            relevant: {
                "summary": {"total_processed": N, ...},
                "timing_stats": {...},
                "results": [{"bill": {...}, "analysis": {...}}, ...]
            }

        Args:
            run_id: Unique identifier for this analysis run
            relevant: Either a list of relevant bills, or a dict with summary/timing_stats/results
            not_relevant: Either a list of not relevant bills, or a dict with summary/timing_stats/results
        """
        pass

    @abstractmethod
    def load_analysis_results(self, run_id: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Load analysis pass results

        Args:
            run_id: Unique identifier for the analysis run

        Returns:
            Tuple of (relevant_bills, not_relevant_bills)

        Raises:
            FileNotFoundError: If results don't exist
        """
        pass

    @abstractmethod
    def get_bill_from_cache(self, bill_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached LegiScan bill data

        Args:
            bill_id: LegiScan bill ID

        Returns:
            Cached bill data if exists, None otherwise
        """
        pass

    @abstractmethod
    def save_bill_to_cache(self, bill_id: int, data: Dict[str, Any]) -> None:
        """
        Save LegiScan bill data to cache

        Args:
            bill_id: LegiScan bill ID
            data: Full bill data from LegiScan API
        """
        pass

    @abstractmethod
    def list_raw_files(self) -> List[str]:
        """
        List available raw data files/identifiers

        Returns:
            List of filenames/identifiers (e.g., ["ct_bills_2025", "in_bills_2025"])
        """
        pass

    @abstractmethod
    def list_filtered_results(self) -> List[str]:
        """
        List available filter result run IDs

        Returns:
            List of run IDs (e.g., ["ct_bills_2025", "filter_results_alan_ct_bills_2025"])
        """
        pass

    @abstractmethod
    def bill_exists_in_raw(self, bill_number: str, filename: str) -> bool:
        """
        Check if a bill exists in raw data

        Args:
            bill_number: Bill number (e.g., "SB01071")
            filename: Raw data filename/identifier

        Returns:
            True if bill exists, False otherwise
        """
        pass

    @abstractmethod
    def get_bill_by_number(self, bill_number: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific bill from raw data by bill number

        Args:
            bill_number: Bill number (e.g., "SB01071")
            filename: Raw data filename/identifier

        Returns:
            Bill data if found, None otherwise
        """
        pass

    @abstractmethod
    def get_bill_text_from_cache(self, doc_id: str) -> Optional[str]:
        """
        Get cached LegiScan bill text data

        Args:
            doc_id: LegiScan document ID

        Returns:
            Cached bill text if exists, None otherwise
        """
        pass

    @abstractmethod
    def save_bill_text_to_cache(self, doc_id: str, text: str) -> None:
        """
        Save LegiScan bill text to cache

        Args:
            doc_id: LegiScan document ID
            text: Full bill text content
        """
        pass


class StorageProviderFactory:
    """Factory for creating storage provider instances based on configuration"""

    @staticmethod
    def create(config: Dict[str, Any]) -> StorageProvider:
        """
        Create a storage provider based on configuration

        Args:
            config: Configuration dictionary with storage settings

        Returns:
            Configured StorageProvider instance

        Raises:
            ValueError: If backend type is unknown or configuration is invalid
        """
        storage_config = config.get('storage', {})
        backend = storage_config.get('backend', 'local')

        if backend == 'local':
            from src.local_file_storage import LocalFileStorage
            local_config = storage_config.get('local', {})
            return LocalFileStorage(local_config)

        elif backend == 'azure_blob':
            from src.azure_blob_storage import AzureBlobStorage
            azure_config = storage_config.get('azure_blob', {})
            return AzureBlobStorage(azure_config)

        elif backend == 'database':
            from src.database_storage import DatabaseStorage
            db_config = storage_config.get('database', {})
            return DatabaseStorage(db_config)

        else:
            raise ValueError(f"Unknown storage backend: {backend}")

    @staticmethod
    def create_from_env(config: Optional[Dict[str, Any]] = None) -> StorageProvider:
        """
        Create storage provider from environment variables and optional config

        Environment variables:
            STORAGE_BACKEND: Backend type (local, azure_blob, database)

        Args:
            config: Optional configuration dictionary (loads from config.json if None)

        Returns:
            Configured StorageProvider instance
        """
        import os
        import json
        from pathlib import Path

        # Load config if not provided
        if config is None:
            config_path = Path(__file__).parent.parent / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

        # Override backend from environment variable
        env_backend = os.getenv('STORAGE_BACKEND')
        if env_backend:
            if 'storage' not in config:
                config['storage'] = {}
            config['storage']['backend'] = env_backend

        return StorageProviderFactory.create(config)
