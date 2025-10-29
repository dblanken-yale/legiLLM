"""
Azure Blob Storage Provider

Implements Azure Blob Storage backend for cloud-based file storage.
Mirrors the local file structure but stores data in Azure Blob containers.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple

from src.storage_provider import StorageProvider


class AzureBlobStorage(StorageProvider):
    """Azure Blob Storage provider for cloud file storage"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure Blob Storage provider

        Args:
            config: Configuration dictionary with:
                - connection_string_env: Environment variable name for connection string
                - container_name: Blob container name
        """
        from azure.storage.blob import BlobServiceClient

        # Get connection string from environment
        connection_string_env = config.get('connection_string_env', 'AZURE_STORAGE_CONNECTION_STRING')
        connection_string = os.getenv(connection_string_env)

        if not connection_string:
            raise ValueError(f"Azure Storage connection string not found in environment variable: {connection_string_env}")

        self.container_name = config.get('container_name', 'legiscan-data')

        # Initialize blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Ensure container exists
        try:
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            if not self.container_client.exists():
                self.container_client.create_container()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Azure Blob Storage container: {e}")

        # Define blob path prefixes (mirrors local directory structure)
        self.raw_prefix = 'raw/'
        self.filtered_prefix = 'filtered/'
        self.analyzed_prefix = 'analyzed/'
        self.cache_prefix = 'cache/legiscan_cache/'

    def _get_blob_client(self, blob_path: str):
        """Get blob client for a specific blob path"""
        return self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )

    def _upload_json(self, blob_path: str, data: Dict[str, Any]) -> None:
        """Upload JSON data to blob storage"""
        blob_client = self._get_blob_client(blob_path)
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        blob_client.upload_blob(json_data, overwrite=True)

    def _download_json(self, blob_path: str) -> Dict[str, Any]:
        """Download JSON data from blob storage"""
        blob_client = self._get_blob_client(blob_path)

        if not blob_client.exists():
            raise FileNotFoundError(f"Blob not found: {blob_path}")

        download_stream = blob_client.download_blob()
        json_data = download_stream.readall().decode('utf-8')
        return json.loads(json_data)

    def _blob_exists(self, blob_path: str) -> bool:
        """Check if a blob exists"""
        blob_client = self._get_blob_client(blob_path)
        return blob_client.exists()

    def _list_blobs(self, prefix: str) -> List[str]:
        """List all blobs with a given prefix"""
        blob_list = self.container_client.list_blobs(name_starts_with=prefix)
        return [blob.name for blob in blob_list]

    def save_raw_data(self, filename: str, data: Dict[str, Any]) -> None:
        """Save raw bill data to raw/{filename}.json"""
        if filename.endswith('.json'):
            filename = filename[:-5]

        blob_path = f"{self.raw_prefix}{filename}.json"
        self._upload_json(blob_path, data)

    def load_raw_data(self, filename: str) -> Dict[str, Any]:
        """Load raw bill data from raw/{filename}.json"""
        if filename.endswith('.json'):
            filename = filename[:-5]

        blob_path = f"{self.raw_prefix}{filename}.json"
        return self._download_json(blob_path)

    def save_filtered_results(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save filter results to filtered/filter_results_{run_id}.json"""
        if run_id.startswith('filter_results_'):
            filename = run_id
        else:
            filename = f"filter_results_{run_id}"

        if filename.endswith('.json'):
            filename = filename[:-5]

        blob_path = f"{self.filtered_prefix}{filename}.json"
        self._upload_json(blob_path, data)

    def load_filtered_results(self, run_id: str) -> Dict[str, Any]:
        """Load filter results from filtered/filter_results_{run_id}.json"""
        # Try different filename patterns
        possible_filenames = [
            run_id,
            f"filter_results_{run_id}",
            f"{run_id}.json",
            f"filter_results_{run_id}.json"
        ]

        for filename in possible_filenames:
            if filename.endswith('.json'):
                blob_path = f"{self.filtered_prefix}{filename}"
            else:
                blob_path = f"{self.filtered_prefix}{filename}.json"

            if self._blob_exists(blob_path):
                return self._download_json(blob_path)

        raise FileNotFoundError(f"Filter results not found for run_id: {run_id}")

    def save_analysis_results(
        self,
        run_id: str,
        relevant: List[Dict[str, Any]],
        not_relevant: List[Dict[str, Any]]
    ) -> None:
        """
        Save analysis results to:
        - analyzed/analysis_{run_id}_relevant.json
        - analyzed/analysis_{run_id}_not_relevant.json
        """
        if run_id.startswith('analysis_'):
            prefix = run_id
        else:
            prefix = f"analysis_{run_id}"

        if prefix.endswith('.json'):
            prefix = prefix[:-5]

        # Save relevant bills
        relevant_path = f"{self.analyzed_prefix}{prefix}_relevant.json"
        self._upload_json(relevant_path, relevant)

        # Save not relevant bills
        not_relevant_path = f"{self.analyzed_prefix}{prefix}_not_relevant.json"
        self._upload_json(not_relevant_path, not_relevant)

    def load_analysis_results(self, run_id: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Load analysis results from:
        - analyzed/analysis_{run_id}_relevant.json
        - analyzed/analysis_{run_id}_not_relevant.json
        """
        if run_id.startswith('analysis_'):
            prefix = run_id
        else:
            prefix = f"analysis_{run_id}"

        if prefix.endswith('.json'):
            prefix = prefix[:-5]

        relevant_path = f"{self.analyzed_prefix}{prefix}_relevant.json"
        not_relevant_path = f"{self.analyzed_prefix}{prefix}_not_relevant.json"

        # Load relevant bills
        if self._blob_exists(relevant_path):
            relevant = self._download_json(relevant_path)
        else:
            relevant = []

        # Load not relevant bills
        if self._blob_exists(not_relevant_path):
            not_relevant = self._download_json(not_relevant_path)
        else:
            not_relevant = []

        if not relevant and not not_relevant:
            raise FileNotFoundError(f"Analysis results not found for run_id: {run_id}")

        return relevant, not_relevant

    def get_bill_from_cache(self, bill_id: int) -> Optional[Dict[str, Any]]:
        """Get cached bill from cache/legiscan_cache/bill_{bill_id}.json"""
        cache_path = f"{self.cache_prefix}bill_{bill_id}.json"

        if not self._blob_exists(cache_path):
            return None

        return self._download_json(cache_path)

    def save_bill_to_cache(self, bill_id: int, data: Dict[str, Any]) -> None:
        """Save bill to cache at cache/legiscan_cache/bill_{bill_id}.json"""
        cache_path = f"{self.cache_prefix}bill_{bill_id}.json"
        self._upload_json(cache_path, data)

    def list_raw_files(self) -> List[str]:
        """List all JSON files in raw/ prefix"""
        blobs = self._list_blobs(self.raw_prefix)

        files = []
        for blob_name in blobs:
            if blob_name.endswith('.json'):
                # Extract filename without prefix and .json extension
                filename = blob_name[len(self.raw_prefix):-5]
                files.append(filename)

        return sorted(files)

    def list_filtered_results(self) -> List[str]:
        """List all filter result files in filtered/ prefix"""
        blobs = self._list_blobs(self.filtered_prefix)

        files = []
        for blob_name in blobs:
            if blob_name.endswith('.json'):
                # Extract filename without prefix and .json extension
                filename = blob_name[len(self.filtered_prefix):-5]
                files.append(filename)

        return sorted(files)

    def bill_exists_in_raw(self, bill_number: str, filename: str) -> bool:
        """Check if a bill exists in raw data by bill number"""
        try:
            data = self.load_raw_data(filename)

            # Handle different data structures
            if isinstance(data, dict):
                if 'summary' in data and 'masterlist' in data['summary']:
                    bills = data['summary']['masterlist']
                elif 'bills' in data:
                    bills = data['bills']
                else:
                    bills = list(data.values()) if data else []
            elif isinstance(data, list):
                bills = data
            else:
                return False

            # Search for bill by number
            for bill in bills:
                if isinstance(bill, dict) and bill.get('bill_number') == bill_number:
                    return True

            return False

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False

    def get_bill_by_number(self, bill_number: str, filename: str) -> Optional[Dict[str, Any]]:
        """Get a specific bill from raw data by bill number"""
        try:
            data = self.load_raw_data(filename)

            # Handle different data structures
            if isinstance(data, dict):
                if 'summary' in data and 'masterlist' in data['summary']:
                    bills = data['summary']['masterlist']
                elif 'bills' in data:
                    bills = data['bills']
                else:
                    bills = list(data.values()) if data else []
            elif isinstance(data, list):
                bills = data
            else:
                return None

            # Search for bill by number
            for bill in bills:
                if isinstance(bill, dict) and bill.get('bill_number') == bill_number:
                    return bill

            return None

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
