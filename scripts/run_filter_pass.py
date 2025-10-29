#!/usr/bin/env python3
"""
Filter Pass Script - First pass of two-stage AI pipeline
Tests the filter with bills from JSON file (LegiScan data)
Uses batch processing - splits large files into manageable chunks
"""

import os
import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_filter_pass import AIFilterPass
from src.storage_provider import StorageProviderFactory

# Default configuration (can be overridden by config.json)
DEFAULT_BATCH_SIZE = 50  # Process 50 bills per API call
DEFAULT_TIMEOUT = 180  # 3 minutes timeout per batch


def load_config():
    """Load configuration from config.json (optional - uses defaults if not found)"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_file = project_root / 'config.json'

    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Config file not found, using default settings")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing config.json: {e}")
        print("Using default settings")
        return {}

def parse_bills_data(data):
    """
    Parse bills data from various JSON formats.

    Args:
        data: Raw JSON data (can be array or LegiScan API response)

    Returns:
        List of bill dictionaries
    """
    bills = []

    # Format 1: Simple array of bills (from fetch_legiscan_bills.py)
    if isinstance(data, list):
        return data

    # Format 2: LegiScan API response with searchresult
    if isinstance(data, dict) and data.get('status') == 'OK':
        searchresult = data.get('searchresult', {})

        # Bills are in numbered keys (0, 1, 2, ...)
        for key, value in searchresult.items():
            if key == 'summary':
                continue

            if isinstance(value, dict) and 'bill_number' in value:
                bill = {
                    'bill_id': value.get('bill_id'),
                    'bill_number': value.get('bill_number'),
                    'title': value.get('title', ''),
                    'description': value.get('description', value.get('title', '')),
                    'url': value.get('url', '')
                }
                bills.append(bill)

    return bills

def main():
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Load configuration
    config = load_config()
    filter_config = config.get('filter_pass', {})
    batch_size = filter_config.get('batch_size', DEFAULT_BATCH_SIZE)
    timeout = filter_config.get('timeout', DEFAULT_TIMEOUT)

    print(f"Configuration: batch_size={batch_size}, timeout={timeout}s")

    # Initialize storage provider
    try:
        storage_provider = StorageProviderFactory.create_from_env(config)
        print(f"Using storage backend: {type(storage_provider).__name__}")
    except Exception as e:
        print(f"ERROR: Could not initialize storage provider: {e}")
        return

    # Get input file from command line or use default
    input_filename = sys.argv[1] if len(sys.argv) > 1 else 'ct_bills_2025'
    # Remove .json extension if provided
    if input_filename.endswith('.json'):
        input_filename = input_filename[:-5]

    # Get API key from environment
    api_key = os.getenv('PORTKEY_API_KEY')

    if not api_key:
        print("ERROR: PORTKEY_API_KEY environment variable not set")
        print("Set it with: export PORTKEY_API_KEY='your-key'")
        return

    # Initialize the filter pass with configured timeout
    print("Initializing AI Filter Pass...")
    filter_pass = AIFilterPass(api_key=api_key, timeout=timeout)

    # Read data from storage provider
    print(f"Reading data from storage: {input_filename}...")
    try:
        data = storage_provider.load_raw_data(input_filename)
        raw_data = json.dumps(data)
    except FileNotFoundError:
        print(f"ERROR: {input_filename} not found in storage")
        print(f"Usage: python run_filter_pass.py [input_file]")
        print(f"Available files: {storage_provider.list_raw_files()}")
        return
    except Exception as e:
        print(f"ERROR: Could not load data: {e}")
        return

    # Parse the data for bill count and lookup
    print("\nParsing JSON data...")
    try:
        bills = parse_bills_data(data)

        if not bills:
            print("ERROR: No bills found in file")
            print("Make sure the file contains valid bill data (JSON array or LegiScan API response)")
            return

        print(f"Found {len(bills)} bills in file")

        # Create lookup dictionary by bill_number
        bills_by_number = {bill['bill_number']: bill for bill in bills}

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON: {e}")
        return

    # Process bills in batches
    print("\n" + "=" * 80)
    print(f"BATCH FILTERING (Processing {batch_size} bills per API call)")
    print("=" * 80)

    all_results = []
    num_batches = (len(bills) + batch_size - 1) // batch_size

    print(f"\nProcessing {len(bills)} bills in {num_batches} batches...")

    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(bills))
        batch_bills = bills[start_idx:end_idx]

        print(f"\n[Batch {batch_num + 1}/{num_batches}] Processing bills {start_idx + 1}-{end_idx}...")

        try:
            # Convert batch to JSON string
            batch_json = json.dumps(batch_bills, indent=2)

            # Process batch
            batch_result = filter_pass.filter_batch(batch_json)
            batch_results = batch_result.get('results', [])

            print(f"  Received {len(batch_results)} results")

            # Display findings from this batch in real-time
            batch_relevant = 0
            for result in batch_results:
                bill_number = result.get('bill_identifier', 'Unknown')
                is_relevant = result.get('relevant', False)
                reason = result.get('reason', 'No reason provided')

                if is_relevant:
                    batch_relevant += 1
                    # Get bill info for display
                    bill = bills_by_number.get(bill_number, {'title': 'Unknown'})
                    print(f"  ✓ RELEVANT: {bill_number} - {bill['title'][:60]}...")
                    print(f"    → {reason[:80]}...")

            if batch_relevant > 0:
                print(f"  Found {batch_relevant} relevant bill(s) in this batch")
            else:
                print(f"  No relevant bills in this batch")

            all_results.extend(batch_results)

            # Small delay between batches to avoid rate limiting
            if batch_num < num_batches - 1:
                time.sleep(1)

        except Exception as e:
            print(f"  ERROR processing batch: {e}")
            print(f"  Skipping batch {batch_num + 1}")
            continue

    # Organize results
    print("\n" + "=" * 80)
    print("ORGANIZING RESULTS")
    print("=" * 80)

    relevant_bills = []
    not_relevant_bills = []

    for result in all_results:
        bill_number = result.get('bill_identifier', 'Unknown')
        is_relevant = result.get('relevant', False)
        reason = result.get('reason', 'No reason provided')

        # Get full bill info from lookup
        bill = bills_by_number.get(bill_number, {
            'bill_number': bill_number,
            'title': 'Unknown',
            'url': 'N/A'
        })

        result_item = {
            'bill': bill,
            'reason': reason
        }

        if is_relevant:
            relevant_bills.append(result_item)
        else:
            not_relevant_bills.append(result_item)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total bills analyzed: {len(all_results)}")
    print(f"Relevant bills: {len(relevant_bills)}")
    print(f"Not relevant bills: {len(not_relevant_bills)}")

    if relevant_bills:
        print("\n" + "=" * 80)
        print("RELEVANT BILLS (Palliative Care Related)")
        print("=" * 80)
        for item in relevant_bills:
            bill = item['bill']
            reason = item['reason']
            print(f"\n{bill['bill_number']}: {bill['title']}")
            print(f"  Reason: {reason}")
            print(f"  URL: {bill.get('url', 'N/A')}")

    # Save results via storage provider
    output_data = {
        'summary': {
            'total_analyzed': len(all_results),
            'relevant_count': len(relevant_bills),
            'not_relevant_count': len(not_relevant_bills),
            'source_file': input_filename
        },
        'relevant_bills': [
            {
                'bill_number': item['bill']['bill_number'],
                'title': item['bill']['title'],
                'url': item['bill'].get('url', 'N/A'),
                'reason': item['reason']
            }
            for item in relevant_bills
        ],
        'not_relevant_bills': [
            {
                'bill_number': item['bill']['bill_number'],
                'title': item['bill']['title'],
                'url': item['bill'].get('url', 'N/A'),
                'reason': item['reason']
            }
            for item in not_relevant_bills
        ]
    }

    try:
        storage_provider.save_filtered_results(input_filename, output_data)
        print(f"\n\nResults saved to storage: filter_results_{input_filename}")
    except Exception as e:
        print(f"\n\nERROR saving results: {e}")

if __name__ == "__main__":
    main()
