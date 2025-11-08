"""
Local File Storage Provider

Implements file-based storage using the existing data/ directory structure.
This is the default storage provider and maintains backward compatibility.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from src.storage_provider import StorageProvider


class LocalFileStorage(StorageProvider):
    """File-based storage provider using local data/ directory"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize local file storage

        Args:
            config: Configuration dictionary with 'data_directory' key
        """
        config = config or {}
        self.data_directory = Path(config.get('data_directory', 'data'))

        # Create directory structure
        self.raw_dir = self.data_directory / 'raw'
        self.filtered_dir = self.data_directory / 'filtered'
        self.analyzed_dir = self.data_directory / 'analyzed'
        self.cache_dir = self.data_directory / 'cache' / 'legiscan_cache'

        # Ensure directories exist
        for directory in [self.raw_dir, self.filtered_dir, self.analyzed_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_raw_data(self, filename: str, data: Dict[str, Any]) -> None:
        """Save raw bill data to data/raw/{filename}.json"""
        # Remove .json extension if provided
        if filename.endswith('.json'):
            filename = filename[:-5]

        filepath = self.raw_dir / f"{filename}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_raw_data(self, filename: str) -> Dict[str, Any]:
        """Load raw bill data from data/raw/{filename}.json"""
        # Remove .json extension if provided
        if filename.endswith('.json'):
            filename = filename[:-5]

        filepath = self.raw_dir / f"{filename}.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Raw data file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_filtered_results(self, run_id: str, data: Dict[str, Any]) -> None:
        """Save filter results to data/filtered/filter_results_{run_id}.json"""
        # Remove filter_results_ prefix if already provided
        if run_id.startswith('filter_results_'):
            filename = run_id
        else:
            filename = f"filter_results_{run_id}"

        # Remove .json extension if provided
        if filename.endswith('.json'):
            filename = filename[:-5]

        filepath = self.filtered_dir / f"{filename}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_filtered_results(self, run_id: str) -> Dict[str, Any]:
        """Load filter results from data/filtered/filter_results_{run_id}.json"""
        # Try different filename patterns
        possible_filenames = [
            run_id,  # Exact match
            f"filter_results_{run_id}",  # With prefix
            f"{run_id}.json",  # With extension
            f"filter_results_{run_id}.json"  # With both
        ]

        for filename in possible_filenames:
            if filename.endswith('.json'):
                filepath = self.filtered_dir / filename
            else:
                filepath = self.filtered_dir / f"{filename}.json"

            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)

        raise FileNotFoundError(f"Filter results not found for run_id: {run_id}")

    def save_analysis_results(
        self,
        run_id: str,
        relevant: Union[List[Dict[str, Any]], Dict[str, Any]],
        not_relevant: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Save analysis results to:
        - data/analyzed/analysis_{run_id}_relevant.json
        - data/analyzed/analysis_{run_id}_not_relevant.json

        Accepts either:
        - List format (legacy): [{"bill": {...}, "analysis": {...}}, ...]
        - Dict format (with stats): {"summary": {...}, "timing_stats": {...}, "results": [...]}
        """
        # Determine filename prefix
        if run_id.startswith('analysis_'):
            prefix = run_id
        else:
            prefix = f"analysis_{run_id}"

        # Remove .json if present
        if prefix.endswith('.json'):
            prefix = prefix[:-5]

        # Save relevant bills (handles both list and dict formats automatically)
        relevant_path = self.analyzed_dir / f"{prefix}_relevant.json"
        with open(relevant_path, 'w', encoding='utf-8') as f:
            json.dump(relevant, f, indent=2, ensure_ascii=False)

        # Save not relevant bills (handles both list and dict formats automatically)
        not_relevant_path = self.analyzed_dir / f"{prefix}_not_relevant.json"
        with open(not_relevant_path, 'w', encoding='utf-8') as f:
            json.dump(not_relevant, f, indent=2, ensure_ascii=False)

    def load_analysis_results(self, run_id: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Load analysis results from:
        - data/analyzed/analysis_{run_id}_relevant.json
        - data/analyzed/analysis_{run_id}_not_relevant.json
        """
        # Determine filename prefix
        if run_id.startswith('analysis_'):
            prefix = run_id
        else:
            prefix = f"analysis_{run_id}"

        # Remove .json if present
        if prefix.endswith('.json'):
            prefix = prefix[:-5]

        relevant_path = self.analyzed_dir / f"{prefix}_relevant.json"
        not_relevant_path = self.analyzed_dir / f"{prefix}_not_relevant.json"

        # Load relevant bills
        if relevant_path.exists():
            with open(relevant_path, 'r', encoding='utf-8') as f:
                relevant = json.load(f)
        else:
            relevant = []

        # Load not relevant bills
        if not_relevant_path.exists():
            with open(not_relevant_path, 'r', encoding='utf-8') as f:
                not_relevant = json.load(f)
        else:
            not_relevant = []

        if not relevant and not not_relevant:
            raise FileNotFoundError(f"Analysis results not found for run_id: {run_id}")

        return relevant, not_relevant

    def get_bill_from_cache(self, bill_id: int) -> Optional[Dict[str, Any]]:
        """Get cached bill from data/cache/legiscan_cache/bill_{bill_id}.json"""
        cache_file = self.cache_dir / f"bill_{bill_id}.json"

        if not cache_file.exists():
            return None

        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_bill_to_cache(self, bill_id: int, data: Dict[str, Any]) -> None:
        """Save bill to cache at data/cache/legiscan_cache/bill_{bill_id}.json"""
        cache_file = self.cache_dir / f"bill_{bill_id}.json"

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_raw_files(self) -> List[str]:
        """List all JSON files in data/raw/ directory"""
        if not self.raw_dir.exists():
            return []

        files = []
        for filepath in self.raw_dir.glob('*.json'):
            # Return filename without .json extension
            files.append(filepath.stem)

        return sorted(files)

    def list_filtered_results(self) -> List[str]:
        """List all filter result files in data/filtered/ directory"""
        if not self.filtered_dir.exists():
            return []

        files = []
        for filepath in self.filtered_dir.glob('*.json'):
            # Return filename without .json extension
            files.append(filepath.stem)

        return sorted(files)

    def bill_exists_in_raw(self, bill_number: str, filename: str) -> bool:
        """Check if a bill exists in raw data by bill number"""
        try:
            data = self.load_raw_data(filename)

            # Handle different data structures
            if isinstance(data, dict):
                # Check if it's a summary with masterlist
                if 'summary' in data and 'masterlist' in data['summary']:
                    bills = data['summary']['masterlist']
                # Check if it has a direct list of bills
                elif 'bills' in data:
                    bills = data['bills']
                # Assume the dict values are bills
                else:
                    bills = data.values() if not isinstance(list(data.values())[0], dict) else data
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
                # Check if it's a summary with masterlist
                if 'summary' in data and 'masterlist' in data['summary']:
                    bills = data['summary']['masterlist']
                # Check if it has a direct list of bills
                elif 'bills' in data:
                    bills = data['bills']
                # Assume the dict values are bills
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

    def get_bill_text_from_cache(self, doc_id: str) -> Optional[str]:
        """Get cached bill text from data/cache/legiscan_cache/bill_text_{doc_id}.txt"""
        cache_file = self.cache_dir / f"bill_text_{doc_id}.txt"

        if not cache_file.exists():
            return None

        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()

    def save_bill_text_to_cache(self, doc_id: str, text: str) -> None:
        """Save bill text to cache at data/cache/legiscan_cache/bill_text_{doc_id}.txt"""
        cache_file = self.cache_dir / f"bill_text_{doc_id}.txt"

        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(text)
