#!/usr/bin/env python3
"""
Test script for bill text fetching functionality
Tests the new getBillText API integration
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

# Load environment variables
load_dotenv()

from src.ai_analysis_pass import AIAnalysisPass
from src.storage_provider import StorageProviderFactory

def main():
    """Test bill text fetching with a single bill"""

    # Initialize storage provider
    storage_provider = StorageProviderFactory.create_from_env()

    # Get LegiScan API key
    legiscan_api_key = os.getenv('LEGISCAN_API_KEY')
    if not legiscan_api_key:
        print("ERROR: LEGISCAN_API_KEY environment variable not set")
        return

    # Initialize analyzer with storage provider
    analyzer = AIAnalysisPass(
        legiscan_api_key=legiscan_api_key,
        storage_provider=storage_provider,
        api_delay=1.0  # 1 second delay between API calls
    )

    print("=" * 80)
    print("Testing Bill Text Fetching")
    print("=" * 80)

    # Test with a known bill from CT 2025
    # Using bill_id from the raw data
    test_bill_id = 1932259  # Example bill_id from CT 2025

    print(f"\nFetching bill {test_bill_id}...")
    bill_data = analyzer._fetch_bill_from_legiscan(test_bill_id)

    if not bill_data:
        print(f"ERROR: Could not fetch bill {test_bill_id}")
        return

    print(f"\nBill Number: {bill_data.get('bill_number')}")
    print(f"Title: {bill_data.get('title')}")

    # Check for text documents
    texts = bill_data.get('texts', [])
    print(f"\nFound {len(texts)} text version(s)")

    if texts:
        latest_text = texts[-1]
        doc_id = latest_text.get('doc_id')
        print(f"Latest text version: {latest_text.get('type')}")
        print(f"Document ID: {doc_id}")

        if doc_id:
            print(f"\nFetching bill text for doc_id {doc_id}...")
            bill_text = analyzer._fetch_bill_text_from_legiscan(test_bill_id, str(doc_id))

            if bill_text:
                print(f"\n{'=' * 80}")
                print("BILL TEXT FETCHED SUCCESSFULLY")
                print(f"{'=' * 80}")
                print(f"Text length: {len(bill_text)} characters")
                print(f"\nFirst 500 characters:")
                print(bill_text[:500])
                print(f"\n{'=' * 80}")

                # Test full extraction
                print("\nTesting full _extract_bill_text()...")
                full_text = analyzer._extract_bill_text(bill_data)
                print(f"Full extracted text length: {len(full_text)} characters")
                print(f"\nFirst 1000 characters of extracted text:")
                print(full_text[:1000])
            else:
                print("ERROR: Could not fetch bill text")
    else:
        print("No text versions available for this bill")

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()
