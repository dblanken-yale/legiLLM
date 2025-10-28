#!/usr/bin/env python3
"""
Format Normalizer - Utilities for handling multiple filter result formats
Supports both AI-filtered and vector similarity-filtered bill data
"""

import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_format(data: Dict) -> str:
    """
    Detect which filter result format is being used.

    Args:
        data: Parsed JSON data from filter results file

    Returns:
        'original' for AI-filtered format with 'relevant_bills'
        'alan' for vector similarity format with 'results'

    Raises:
        ValueError: If format cannot be determined
    """
    if 'relevant_bills' in data:
        return 'original'
    elif 'results' in data:
        return 'alan'
    else:
        raise ValueError(
            "Unknown filter format. Expected 'relevant_bills' or 'results' field in JSON. "
            f"Found keys: {list(data.keys())}"
        )


def normalize_filter_results(data: Dict) -> List[Dict]:
    """
    Normalize filter results from either format to a common structure.

    Args:
        data: Parsed JSON data from filter results file

    Returns:
        List of normalized bill dictionaries with standardized fields:
        - bill_number: str (standardized from 'bill_number' or 'number')
        - title: str
        - url: str
        - reason: str (from original format, or generated from similarity score)
        - extra_metadata: dict (any additional fields from source format)

    Raises:
        ValueError: If format cannot be determined or is invalid
    """
    format_type = detect_format(data)
    logger.info(f"Detected filter format: {format_type}")

    if format_type == 'original':
        return _normalize_original_format(data)
    elif format_type == 'alan':
        return _normalize_alan_format(data)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def _normalize_original_format(data: Dict) -> List[Dict]:
    """
    Normalize the original AI-filtered format.

    Original format structure:
    {
      "summary": {...},
      "relevant_bills": [
        {
          "bill_number": "SB00123",
          "title": "...",
          "url": "...",
          "reason": "..."
        }
      ]
    }
    """
    bills = data.get('relevant_bills', [])
    logger.info(f"Normalizing {len(bills)} bills from original format")

    normalized = []
    for bill in bills:
        normalized_bill = {
            'bill_number': bill.get('bill_number'),
            'title': bill.get('title'),
            'url': bill.get('url'),
            'reason': bill.get('reason'),
            'extra_metadata': {}
        }
        normalized.append(normalized_bill)

    return normalized


def _normalize_alan_format(data: Dict) -> List[Dict]:
    """
    Normalize Alan's vector similarity format.

    Alan's format structure:
    {
      "total_results": 8,
      "results": [
        {
          "bill_id": "1932259",
          "number": "SB01071",
          "title": "...",
          "url": "...",
          "status_date": "2025-01-22",
          "last_action": "...",
          "year": "2025",
          "session": "2025 Regular Session",
          "similarity_score": 0.524,
          "distance": 0.907
        }
      ]
    }
    """
    bills = data.get('results', [])
    total = data.get('total_results', len(bills))
    logger.info(f"Normalizing {len(bills)} bills from Alan's format (total_results: {total})")

    normalized = []
    for bill in bills:
        # Generate a reason string from similarity score
        similarity_score = bill.get('similarity_score', 0)
        distance = bill.get('distance', 0)
        reason = f"Vector similarity match (score: {similarity_score:.4f}, distance: {distance:.4f})"

        normalized_bill = {
            'bill_number': bill.get('number'),  # Map 'number' to 'bill_number'
            'title': bill.get('title'),
            'url': bill.get('url'),
            'reason': reason,
            'extra_metadata': {
                'bill_id': bill.get('bill_id'),
                'status_date': bill.get('status_date'),
                'last_action': bill.get('last_action'),
                'year': bill.get('year'),
                'session': bill.get('session'),
                'similarity_score': similarity_score,
                'distance': distance
            }
        }
        normalized.append(normalized_bill)

    return normalized


def get_format_info(data: Dict) -> Dict[str, Any]:
    """
    Get information about the filter format and contents.

    Args:
        data: Parsed JSON data from filter results file

    Returns:
        Dictionary with format metadata:
        - format: str ('original' or 'alan')
        - bill_count: int
        - has_summary: bool
        - has_similarity_scores: bool
        - fields: list of field names present in bills
    """
    format_type = detect_format(data)

    if format_type == 'original':
        bills = data.get('relevant_bills', [])
        has_summary = 'summary' in data
        has_similarity = False
    else:  # alan
        bills = data.get('results', [])
        has_summary = False
        has_similarity = True

    # Get field names from first bill
    fields = list(bills[0].keys()) if bills else []

    return {
        'format': format_type,
        'bill_count': len(bills),
        'has_summary': has_summary,
        'has_similarity_scores': has_similarity,
        'fields': fields
    }
