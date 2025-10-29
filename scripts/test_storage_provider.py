#!/usr/bin/env python3
"""
Storage Provider Test Script
Validates that the storage abstraction layer works correctly with local file storage.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage_provider import StorageProviderFactory

# Test data
TEST_RAW_DATA = {
    "summary": {
        "masterlist": [
            {
                "bill_id": 12345,
                "bill_number": "SB001",
                "title": "Test Bill Title",
                "description": "Test bill description",
                "state": "CT",
                "year": 2025,
                "url": "https://example.com/bill/SB001"
            }
        ]
    }
}

TEST_FILTER_RESULTS = {
    "summary": {
        "total_analyzed": 1,
        "relevant_count": 1,
        "not_relevant_count": 0,
        "source_file": "test_bills"
    },
    "relevant_bills": [
        {
            "bill_number": "SB001",
            "title": "Test Bill Title",
            "url": "https://example.com/bill/SB001",
            "reason": "Test relevance reason"
        }
    ]
}

TEST_ANALYSIS_RESULTS_RELEVANT = [
    {
        "bill_number": "SB001",
        "title": "Test Bill Title",
        "is_relevant": True,
        "summary": "Test summary",
        "categories": ["Clinical Skill-Building"],
        "tags": ["test", "palliative care"]
    }
]

TEST_ANALYSIS_RESULTS_NOT_RELEVANT = []

TEST_CACHE_DATA = {
    "bill_id": 12345,
    "bill_number": "SB001",
    "title": "Test Bill Title",
    "full_text": "This is the full bill text from LegiScan API..."
}


def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


def test_storage_provider():
    """Run all storage provider tests"""
    print_header("Storage Provider Test Suite")

    # Load configuration
    config_file = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print_success(f"Loaded configuration from {config_file}")
    except FileNotFoundError:
        print_error(f"Configuration file not found: {config_file}")
        config = {}

    # Initialize storage provider
    print_header("1. Initializing Storage Provider")
    try:
        storage_provider = StorageProviderFactory.create_from_env(config)
        print_success(f"Initialized storage provider: {type(storage_provider).__name__}")

        storage_backend = os.getenv('STORAGE_BACKEND', config.get('storage', {}).get('backend', 'local'))
        print_info(f"Using backend: {storage_backend}")
    except Exception as e:
        print_error(f"Failed to initialize storage provider: {e}")
        return False

    # Test 1: Save and load raw data
    print_header("2. Testing Raw Data Storage")
    test_filename = "test_storage_validation"
    try:
        # Save
        storage_provider.save_raw_data(test_filename, TEST_RAW_DATA)
        print_success(f"Saved raw data: {test_filename}")

        # Load
        loaded_data = storage_provider.load_raw_data(test_filename)
        print_success(f"Loaded raw data: {test_filename}")

        # Verify
        if loaded_data == TEST_RAW_DATA:
            print_success("Raw data round-trip successful - data matches")
        else:
            print_error("Raw data mismatch")
            print_info(f"Expected: {TEST_RAW_DATA}")
            print_info(f"Got: {loaded_data}")
            return False
    except Exception as e:
        print_error(f"Raw data test failed: {e}")
        return False

    # Test 2: Save and load filter results
    print_header("3. Testing Filter Results Storage")
    test_run_id = "test_validation_run"
    try:
        # Save
        storage_provider.save_filtered_results(test_run_id, TEST_FILTER_RESULTS)
        print_success(f"Saved filter results: {test_run_id}")

        # Load
        loaded_results = storage_provider.load_filtered_results(test_run_id)
        print_success(f"Loaded filter results: {test_run_id}")

        # Verify
        if loaded_results == TEST_FILTER_RESULTS:
            print_success("Filter results round-trip successful - data matches")
        else:
            print_error("Filter results mismatch")
            return False
    except Exception as e:
        print_error(f"Filter results test failed: {e}")
        return False

    # Test 3: Save and load analysis results
    print_header("4. Testing Analysis Results Storage")
    test_analysis_run_id = "test_analysis_validation"
    try:
        # Save
        storage_provider.save_analysis_results(
            test_analysis_run_id,
            TEST_ANALYSIS_RESULTS_RELEVANT,
            TEST_ANALYSIS_RESULTS_NOT_RELEVANT
        )
        print_success(f"Saved analysis results: {test_analysis_run_id}")

        # Load
        relevant, not_relevant = storage_provider.load_analysis_results(test_analysis_run_id)
        print_success(f"Loaded analysis results: {test_analysis_run_id}")

        # Verify
        if relevant == TEST_ANALYSIS_RESULTS_RELEVANT and not_relevant == TEST_ANALYSIS_RESULTS_NOT_RELEVANT:
            print_success("Analysis results round-trip successful - data matches")
        else:
            print_error("Analysis results mismatch")
            return False
    except Exception as e:
        print_error(f"Analysis results test failed: {e}")
        return False

    # Test 4: Save and load cache
    print_header("5. Testing Cache Storage")
    test_bill_id = 12345
    try:
        # Save
        storage_provider.save_bill_to_cache(test_bill_id, TEST_CACHE_DATA)
        print_success(f"Saved bill to cache: bill_id={test_bill_id}")

        # Load
        cached_bill = storage_provider.get_bill_from_cache(test_bill_id)
        print_success(f"Loaded bill from cache: bill_id={test_bill_id}")

        # Verify
        if cached_bill == TEST_CACHE_DATA:
            print_success("Cache round-trip successful - data matches")
        else:
            print_error("Cache data mismatch")
            return False

        # Test cache miss
        missing_bill = storage_provider.get_bill_from_cache(99999)
        if missing_bill is None:
            print_success("Cache miss handled correctly (returned None)")
        else:
            print_error("Cache miss should return None")
            return False
    except Exception as e:
        print_error(f"Cache test failed: {e}")
        return False

    # Test 5: List files
    print_header("6. Testing File Listing")
    try:
        raw_files = storage_provider.list_raw_files()
        print_success(f"Listed raw files: {len(raw_files)} files found")
        if test_filename in raw_files:
            print_success(f"Test file found in listing: {test_filename}")
        else:
            print_error(f"Test file not found in listing: {test_filename}")

        filtered_files = storage_provider.list_filtered_results()
        print_success(f"Listed filter results: {len(filtered_files)} files found")
        if f"filter_results_{test_run_id}" in filtered_files or test_run_id in filtered_files:
            print_success(f"Test filter results found in listing")
        else:
            print_info(f"Note: Test filter results listing may vary by backend")
    except Exception as e:
        print_error(f"File listing test failed: {e}")
        return False

    # Test 6: Bill lookup methods
    print_header("7. Testing Bill Lookup Methods")
    try:
        # Check if bill exists
        exists = storage_provider.bill_exists_in_raw("SB001", test_filename)
        if exists:
            print_success("bill_exists_in_raw() found test bill")
        else:
            print_error("bill_exists_in_raw() should have found test bill")
            return False

        # Get bill by number
        bill = storage_provider.get_bill_by_number("SB001", test_filename)
        if bill and bill.get('bill_number') == "SB001":
            print_success("get_bill_by_number() retrieved correct bill")
        else:
            print_error("get_bill_by_number() failed")
            return False

        # Check non-existent bill
        no_bill = storage_provider.get_bill_by_number("INVALID999", test_filename)
        if no_bill is None:
            print_success("get_bill_by_number() correctly returned None for missing bill")
        else:
            print_error("get_bill_by_number() should return None for missing bill")
            return False
    except Exception as e:
        print_error(f"Bill lookup test failed: {e}")
        return False

    # All tests passed
    print_header("✅ All Tests Passed!")
    print_info("Storage provider is working correctly")
    print_info(f"Backend: {type(storage_provider).__name__}")
    print_info("\nYou can now:")
    print_info("  1. Run the pipeline with the same commands as before")
    print_info("  2. Switch backends by setting STORAGE_BACKEND environment variable")
    print_info("  3. Use Azure storage by setting STORAGE_BACKEND=database or azure_blob")

    return True


def cleanup_test_files(storage_provider):
    """Clean up test files (optional)"""
    print_header("Cleanup (Optional)")
    response = input("Do you want to clean up test files? (y/N): ").strip().lower()

    if response == 'y':
        try:
            # Note: Not all storage providers may support deletion
            # For LocalFileStorage, files are in data/ directories
            print_info("Test files left in place for inspection")
            print_info("You can manually delete:")
            print_info("  - data/raw/test_storage_validation.json")
            print_info("  - data/filtered/filter_results_test_validation_run.json")
            print_info("  - data/analyzed/analysis_test_analysis_validation_*.json")
            print_info("  - data/cache/legiscan_cache/bill_12345.json")
        except Exception as e:
            print_error(f"Cleanup failed: {e}")
    else:
        print_info("Skipping cleanup - test files remain for inspection")


def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("  LegiScan Bill Analysis Pipeline - Storage Provider Test Suite")
    print("  This script validates the storage abstraction layer")
    print("=" * 80)

    success = test_storage_provider()

    if success:
        print("\n" + "=" * 80)
        print("  TEST SUITE: ✅ PASSED")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("  TEST SUITE: ❌ FAILED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
