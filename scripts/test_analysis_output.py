#!/usr/bin/env python3
"""
Test that analysis results include full bill text
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
    """Test that analysis includes full bill text"""

    # Initialize storage provider
    storage_provider = StorageProviderFactory.create_from_env()

    # Get API keys
    legiscan_api_key = os.getenv('LEGISCAN_API_KEY')
    portkey_api_key = os.getenv('PORTKEY_API_KEY')

    if not legiscan_api_key or not portkey_api_key:
        print("ERROR: Required API keys not set")
        return

    # Initialize analyzer
    analyzer = AIAnalysisPass(
        api_key=portkey_api_key,
        legiscan_api_key=legiscan_api_key,
        storage_provider=storage_provider,
        api_delay=0.5
    )

    print("=" * 80)
    print("Testing Analysis Output Structure")
    print("=" * 80)

    # Test with a known bill
    test_bill_id = 1932259
    test_bill_data = {
        "bill_number": "SB01071",
        "title": "An Act Implementing The Recommendations Of The Pediatric Hospice Working Group.",
        "url": "https://legiscan.com/CT/bill/SB01071/2025"
    }

    print(f"\nAnalyzing bill {test_bill_data['bill_number']}...")
    analysis = analyzer.analyze_data(test_bill_data, bill_id=test_bill_id)

    print(f"\nAnalysis result keys: {list(analysis.keys())}")

    if 'full_bill_text' in analysis:
        bill_text = analysis['full_bill_text']
        print(f"\n✓ SUCCESS: full_bill_text is present in analysis result")
        print(f"  Length: {len(bill_text)} characters")
        print(f"\n  First 300 characters:")
        print(f"  {bill_text[:300]}")
    else:
        print(f"\n✗ ERROR: full_bill_text is NOT in analysis result")
        print(f"  Available keys: {list(analysis.keys())}")

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()
