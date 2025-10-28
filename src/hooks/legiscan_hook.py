"""
LegiScan Data Enrichment Hook

Fetches full bill details from LegiScan API and appends to analysis data.
"""

import os
import json
import logging
import requests
from typing import Any, Dict, Optional
from pathlib import Path
from src.hook_system import DataHook

logger = logging.getLogger(__name__)

LEGISCAN_API_BASE = "https://api.legiscan.com/"


class LegiScanHook(DataHook):
    """
    Enriches bill data with full text from LegiScan API.

    Fetches complete bill details using LegiScan's getBill operation
    and appends formatted text to the data for AI analysis.
    """

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize LegiScan hook.

        Args:
            api_key: LegiScan API key (defaults to LEGISCAN_API_KEY env var)
            cache_dir: Cache directory for LegiScan responses
        """
        self.api_key = api_key or os.getenv('LEGISCAN_API_KEY')
        self.cache_dir = cache_dir or Path('data/cache/legiscan_cache')

        if self.api_key and self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"LegiScan cache directory: {self.cache_dir}")

    def process(self, data: Any, context: Dict) -> Any:
        """
        Fetch and append LegiScan bill details to data.

        Args:
            data: Input data (string or dict)
            context: Context with item_id

        Returns:
            Enriched data with bill text appended
        """
        if not self.api_key:
            logger.warning("LegiScan API key not set, skipping enrichment")
            return data

        # Extract bill_id from context
        bill_id = context.get('item_id')
        if not bill_id:
            logger.debug("No item_id in context, skipping LegiScan fetch")
            return data

        # Fetch bill from LegiScan
        bill_data = self._fetch_bill(bill_id)
        if not bill_data:
            logger.warning(f"Could not fetch bill {bill_id}, analyzing with metadata only")
            return data

        # Extract and format bill text
        bill_text = self._extract_text(bill_data)

        # Log the fetched content
        logger.info("=" * 80)
        logger.info("FETCHED BILL CONTENT:")
        logger.info(bill_text)
        logger.info("=" * 80)

        # Append to data (match current behavior exactly)
        if isinstance(data, str):
            data += f"\n\n## Full Bill Details from LegiScan API:\n\n{bill_text}"
        elif isinstance(data, dict):
            data['legiscan_full_text'] = bill_text
            data['legiscan_raw'] = bill_data

        return data

    def _fetch_bill(self, bill_id: int) -> Optional[Dict]:
        """
        Fetch full bill details from LegiScan API using getBill operation.
        Uses local file cache to avoid re-fetching the same bill.

        Args:
            bill_id: LegiScan bill ID

        Returns:
            Bill details dict or None if fetch fails
        """
        # Check cache first
        cache_file = self.cache_dir / f"bill_{bill_id}.json"
        if cache_file.exists():
            logger.info(f"Loading bill {bill_id} from cache: {cache_file}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"Successfully loaded bill {bill_id} from cache")
                return cached_data
            except Exception as e:
                logger.warning(f"Error reading cache file for bill {bill_id}: {e}")
                logger.info("Falling back to API fetch...")

        # Fetch from API if not in cache
        try:
            params = {
                'key': self.api_key,
                'op': 'getBill',
                'id': bill_id
            }

            logger.info(f"Fetching bill {bill_id} from LegiScan API...")
            response = requests.get(LEGISCAN_API_BASE, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get('status') == 'OK':
                bill_data = result.get('bill')
                logger.info(f"Successfully fetched bill {bill_id} from API")

                # Save to cache
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(bill_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Cached bill {bill_id} to: {cache_file}")
                except Exception as e:
                    logger.warning(f"Could not save bill {bill_id} to cache: {e}")

                return bill_data
            else:
                logger.error(f"LegiScan API error: {result.get('alert', {}).get('message', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching bill {bill_id} from LegiScan: {e}")
            return None

    def _extract_text(self, bill_data: Dict) -> str:
        """
        Extract readable text from LegiScan bill data.

        Args:
            bill_data: Bill data from LegiScan API

        Returns:
            Formatted bill text with title, description, and metadata
        """
        text_parts = []

        # Add bill metadata
        if bill_data.get('bill_number'):
            text_parts.append(f"Bill Number: {bill_data['bill_number']}")

        if bill_data.get('title'):
            text_parts.append(f"Title: {bill_data['title']}")

        if bill_data.get('description'):
            text_parts.append(f"Description: {bill_data['description']}")

        # Add status info
        if bill_data.get('status'):
            text_parts.append(f"Status: {bill_data['status']}")

        if bill_data.get('status_date'):
            text_parts.append(f"Status Date: {bill_data['status_date']}")

        # Add bill text from documents
        if bill_data.get('texts'):
            texts = bill_data['texts']
            if isinstance(texts, list) and len(texts) > 0:
                # Get the most recent text version
                latest_text = texts[-1]
                if latest_text.get('doc_id'):
                    text_parts.append(f"\nBill Text (Version: {latest_text.get('type', 'Unknown')}):")
                    text_parts.append(f"[Full text document ID: {latest_text['doc_id']}]")

        # Add sponsors
        if bill_data.get('sponsors'):
            sponsors = bill_data['sponsors']
            if isinstance(sponsors, list):
                sponsor_names = [s.get('name', 'Unknown') for s in sponsors[:3]]  # First 3 sponsors
                text_parts.append(f"Sponsors: {', '.join(sponsor_names)}")

        # Add subjects/tags
        if bill_data.get('subjects'):
            subjects = bill_data['subjects']
            if isinstance(subjects, list):
                subject_names = [s.get('subject_name', '') for s in subjects]
                text_parts.append(f"Subjects: {', '.join(subject_names)}")

        return "\n".join(text_parts)

    def get_cache_key(self, data: Any, context: Dict) -> Optional[str]:
        """
        Generate cache key using bill_id.

        Args:
            data: Input data
            context: Context with item_id

        Returns:
            Cache key or None
        """
        bill_id = context.get('item_id')
        if bill_id:
            return f"legiscan_bill_{bill_id}"
        return None
