#!/usr/bin/env python3
"""
LegiScan API Bill Fetcher
Fetches bills from Connecticut using getSearch API with title and description.
"""

import requests
import json
import os
from typing import List, Dict

# Configuration
BASE_URL = "https://api.legiscan.com/"
STATE_CODE = "CT"
YEAR = 2025
OUTPUT_FILE = "ct_bills_2025.json"
SAMPLES_FILE = "test_samples.txt"


def make_api_call(api_key: str, operation: str, **params) -> Dict:
    """
    Make a call to the LegiScan API.

    Args:
        api_key: LegiScan API key
        operation: API operation name
        **params: Additional parameters for the API call

    Returns:
        API response as dictionary
    """
    params_dict = {
        'key': api_key,
        'op': operation,
        **params
    }

    try:
        response = requests.get(BASE_URL, params=params_dict, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return {}


def search_bills(api_key: str, state: str = STATE_CODE, year: int = YEAR, page: int = 1) -> Dict:
    """
    Search for bills using getSearch API.

    Args:
        api_key: LegiScan API key
        state: State code (e.g., 'CT')
        year: Year to search
        page: Page number for pagination

    Returns:
        Search results with bill summaries
    """
    print(f"Searching bills for {state} {year}, page {page}...")

    # Note: getSearch requires a query parameter, but '*' or empty can get all bills
    result = make_api_call(
        api_key,
        'getSearch',
        state=state,
        year=year,
        page=page,
        query='1'  # Use a simple query to get bills (searching for bills with "1" in them)
    )

    return result


def extract_bill_data(bill_summary: Dict) -> Dict:
    """
    Extract relevant fields from bill summary.

    Args:
        bill_summary: Bill summary from search results

    Returns:
        Dictionary with bill_id, bill_number, title, description
    """
    return {
        'bill_id': bill_summary.get('bill_id'),
        'bill_number': bill_summary.get('bill_number', ''),
        'title': bill_summary.get('title', ''),
        'description': bill_summary.get('description', ''),
        'url': bill_summary.get('url', '')
    }


def save_bills_json(bills: List[Dict], output_file: str):
    """
    Save bills to JSON file.

    Args:
        bills: List of bill dictionaries
        output_file: Output filename
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(bills)} bills to {output_file}")


def create_test_samples(bills: List[Dict], samples_file: str, num_samples: int = None):
    """
    Create formatted text samples for testing.

    Args:
        bills: List of bill dictionaries
        samples_file: Output filename
        num_samples: Number of samples to include (None = all bills)
    """
    # If num_samples is None, use all bills
    bills_to_write = bills if num_samples is None else bills[:num_samples]

    with open(samples_file, 'w', encoding='utf-8') as f:
        for idx, bill in enumerate(bills_to_write, 1):
            f.write(f"Bill #{idx}\n")
            f.write(f"Number: {bill['bill_number']}\n")
            f.write(f"Title: {bill['title']}\n")
            f.write(f"Description: {bill['description']}\n")
            f.write("\n" + "=" * 80 + "\n\n")

    print(f"Created {len(bills_to_write)} bill entries in {samples_file}")


def main():
    """
    Main execution function.
    """
    # Get API key from environment
    api_key = os.getenv('LEGISCAN_API_KEY')

    if not api_key:
        print("ERROR: LEGISCAN_API_KEY environment variable not set")
        print("Set it with: export LEGISCAN_API_KEY='your-key'")
        return

    print("=" * 80)
    print(f"LegiScan Bill Fetcher - {STATE_CODE} {YEAR}")
    print("=" * 80)

    # Fetch bills using getSearch with pagination
    all_bills = []
    page = 1
    max_pages = 100  # Safety limit

    while page <= max_pages:
        result = search_bills(api_key, STATE_CODE, YEAR, page)

        if result.get('status') != 'OK':
            alert = result.get('alert', {})
            print(f"Search failed: {alert.get('message', 'Unknown error')}")
            # Debug: print full result
            print(f"Debug - Full API response: {json.dumps(result, indent=2)}")
            break

        searchresult = result.get('searchresult', {})

        # LegiScan API returns bills in numbered keys (0, 1, 2, ...), not in a 'results' array
        # Extract all numeric keys
        bills_found = 0
        for key, value in searchresult.items():
            # Skip non-numeric keys like 'summary', 'page', etc.
            if key.isdigit() and isinstance(value, dict):
                bill_data = extract_bill_data(value)
                all_bills.append(bill_data)
                bills_found += 1

        if bills_found == 0:
            print("No more bills found.")
            break

        print(f"Found {bills_found} bills on page {page}")

        # Check if there are more pages
        # The 'summary' key contains pagination info
        summary_info = searchresult.get('summary', {})
        if isinstance(summary_info, dict):
            # The page field is a string like "1 of 30"
            page_str = summary_info.get('page', f'{page} of 1')
            if ' of ' in str(page_str):
                parts = str(page_str).split(' of ')
                current_page = int(parts[0])
                total_pages = int(parts[1])
            else:
                current_page = page
                total_pages = int(summary_info.get('page_total', 1))

            print(f"Progress: Page {current_page} of {total_pages}")

            if current_page >= total_pages:
                break

        page += 1

    # Save results
    if all_bills:
        print("\n" + "=" * 80)
        print("Saving results...")
        save_bills_json(all_bills, OUTPUT_FILE)
        create_test_samples(all_bills, SAMPLES_FILE)  # Will write all bills (no limit)

        print("\n" + "=" * 80)
        print("COMPLETE!")
        print("=" * 80)
        print(f"Total bills fetched: {len(all_bills)}")
        print(f"Full data (JSON): {OUTPUT_FILE}")
        print(f"Full data (Text): {SAMPLES_FILE}")
        print("\nNext steps:")
        print(f"  1. Review text file: less {SAMPLES_FILE}")
        print(f"  2. Test filter: python test_filter.py {OUTPUT_FILE}")
        print(f"  3. Process all bills: Update config.json to use {OUTPUT_FILE}")
    else:
        print("\n" + "=" * 80)
        print("No bills found!")
        print("=" * 80)


if __name__ == "__main__":
    main()
