#!/usr/bin/env python3
"""
Analysis Pass Script - Second pass of two-stage AI pipeline
Analyzes filtered bills with full text from LegiScan API
Applies comprehensive palliative care categorization framework
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_analysis_pass import AIAnalysisPass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / 'data'
CONFIG_FILE = PROJECT_ROOT / 'config.json'
FILTER_RESULTS_FILE = DATA_DIR / 'filtered' / 'filter_results_ct_bills_2025.json'
SOURCE_BILLS_FILE = DATA_DIR / 'raw' / 'ct_bills_2025.json'
RELEVANT_OUTPUT_FILE = DATA_DIR / 'analyzed' / 'analysis_results_relevant.json'
NOT_RELEVANT_OUTPUT_FILE = DATA_DIR / 'analyzed' / 'analysis_results_not_relevant.json'
LEGISCAN_CACHE_DIR = DATA_DIR / 'cache' / 'legiscan_cache'


def load_config():
    """Load configuration from config.json (optional - uses defaults if not found)"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("Config file not found, using default settings")
        return {}


def load_filter_results():
    """Load filtered bill results"""
    try:
        with open(FILTER_RESULTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Filter results file not found: {FILTER_RESULTS_FILE}")
        raise


def load_source_bills():
    """Load source bills with bill_id"""
    try:
        with open(SOURCE_BILLS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Source bills file not found: {SOURCE_BILLS_FILE}")
        raise


def create_bill_lookup(source_bills):
    """Create lookup dict from bill_number to full bill data including bill_id"""
    return {bill['bill_number']: bill for bill in source_bills}


def format_bill_for_analysis(bill):
    """
    Format bill data for analysis prompt.

    Args:
        bill: Dict with bill_number, title, url, and optionally reason

    Returns:
        Formatted string for analysis (not a dict, since AIAnalysisPass expects to format it)
    """
    formatted = f"""**Bill Number**: {bill['bill_number']}
**Title**: {bill['title']}
**URL**: {bill['url']}"""

    # Include filter reason if present (for bills from filter results)
    if 'reason' in bill:
        formatted += f"\n**Initial Filter Reason**: {bill['reason']}"

    return formatted


def select_test_bills(bills, count=5):
    """
    Select diverse test bills for analysis.

    Tries to pick bills with different characteristics:
    - Explicit palliative care mentions
    - Pediatric hospice
    - Workforce development
    - Payment/Medicaid
    - Indirect impacts

    Args:
        bills: List of bill dictionaries
        count: Number of bills to select

    Returns:
        List of selected bills
    """
    selected = []

    # Priority: Pediatric Hospice (should hit multiple categories)
    for bill in bills:
        if 'pediatric hospice' in bill['title'].lower() or 'pediatric hospice' in bill['reason'].lower():
            selected.append(bill)
            if len(selected) >= count:
                return selected[:count]

    # Priority: Explicit palliative care mentions
    for bill in bills:
        if bill not in selected and 'palliative' in bill['title'].lower():
            selected.append(bill)
            if len(selected) >= count:
                return selected[:count]

    # Priority: Pain medication/symptom management
    for bill in bills:
        if bill not in selected and ('pain medication' in bill['reason'].lower() or 'pain management' in bill['reason'].lower()):
            selected.append(bill)
            if len(selected) >= count:
                return selected[:count]

    # Priority: Workforce development
    for bill in bills:
        if bill not in selected and ('workforce' in bill['reason'].lower() or 'loan forgiveness' in bill['reason'].lower()):
            selected.append(bill)
            if len(selected) >= count:
                return selected[:count]

    # Priority: Medicaid/payment
    for bill in bills:
        if bill not in selected and ('medicaid' in bill['reason'].lower() or 'payment' in bill['reason'].lower()):
            selected.append(bill)
            if len(selected) >= count:
                return selected[:count]

    # Fill remaining slots with any bills
    for bill in bills:
        if bill not in selected:
            selected.append(bill)
            if len(selected) >= count:
                return selected[:count]

    return selected


def main():
    """Main test execution"""
    logger.info("=" * 80)
    logger.info("AI Analysis Pass with Palliative Care Categorization")
    logger.info("=" * 80)

    # Load configuration
    logger.info("\n1. Loading configuration...")
    config = load_config()

    # Check for test mode
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    test_count = int(os.getenv('TEST_COUNT', '5'))

    # Get API key from environment variable (like test_filter.py does)
    api_key = os.getenv('PORTKEY_API_KEY')
    if not api_key:
        logger.error("PORTKEY_API_KEY environment variable not set")
        logger.info("Set it with: export PORTKEY_API_KEY='your-key'")
        return

    # Load filter results (bills that passed first filter)
    logger.info("\n2. Loading filter results...")
    filter_results = load_filter_results()
    filter_relevant_bills = filter_results.get('relevant_bills', [])
    logger.info(f"   Filter pass identified {len(filter_relevant_bills)} potentially relevant bills")

    # Load source bills to get bill_id
    logger.info("\n3. Loading source bills for bill_id lookup...")
    source_bills = load_source_bills()
    bill_lookup = create_bill_lookup(source_bills)
    logger.info(f"   Loaded {len(source_bills)} total bills for lookup")

    # Select bills to process
    if test_mode:
        logger.info(f"\n4. TEST MODE: Selecting {test_count} bills from filter results...")
        bills_to_process = select_test_bills(filter_relevant_bills, count=test_count)
        logger.info(f"   Selected {len(bills_to_process)} bills for testing:")
    else:
        logger.info(f"\n4. PRODUCTION MODE: Re-evaluating all {len(filter_relevant_bills)} filtered bills with full text...")
        bills_to_process = filter_relevant_bills
        logger.info("   To run in test mode, set: export TEST_MODE=true")

    for i, bill in enumerate(bills_to_process[:10], 1):
        logger.info(f"   {i}. {bill['bill_number']}: {bill['title'][:80]}...")
    if len(bills_to_process) > 10:
        logger.info(f"   ... and {len(bills_to_process) - 10} more bills")

    # Get LegiScan API key
    legiscan_api_key = os.getenv('LEGISCAN_API_KEY')
    if not legiscan_api_key:
        logger.warning("LEGISCAN_API_KEY environment variable not set")
        logger.warning("Will analyze bills with metadata only (no full text)")

    # Initialize analyzer
    logger.info("\n5. Initializing AI Analysis Pass...")
    analysis_config = config.get('analysis_pass', {})
    timeout = analysis_config.get('timeout', 90)

    analyzer = AIAnalysisPass(
        api_key=api_key,
        model=config.get('model', 'gpt-4o-mini'),
        temperature=config.get('temperature', 0.3),
        max_tokens=config.get('max_tokens', 2000),  # Increased for bill text
        timeout=timeout,
        legiscan_api_key=legiscan_api_key
    )

    logger.info(f"   Configuration: model={config.get('model', 'gpt-4o-mini')}, "
                f"timeout={timeout}s, max_tokens={config.get('max_tokens', 2000)}")

    # Analyze each bill
    logger.info("\n6. Analyzing bills...")
    relevant_results = []
    not_relevant_results = []

    for i, bill in enumerate(bills_to_process, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Analyzing Bill {i}/{len(bills_to_process)}: {bill['bill_number']}")
        logger.info(f"{'=' * 80}")
        logger.info(f"Title: {bill['title']}")
        logger.info(f"URL: {bill['url']}")

        try:
            # Get bill_id from lookup
            bill_number = bill['bill_number']
            source_bill = bill_lookup.get(bill_number)
            bill_id = source_bill.get('bill_id') if source_bill else None

            if bill_id:
                logger.info(f"Bill ID: {bill_id}")
            else:
                logger.warning(f"Could not find bill_id for {bill_number}, skipping")
                continue

            # Format bill data for analysis
            bill_data = format_bill_for_analysis(bill)

            # Analyze (pass bill_id for LegiScan API fetch)
            analysis = analyzer.analyze_data(bill_data, bill_id=bill_id)

            # Add bill info to results
            result = {
                'bill': bill,
                'analysis': analysis
            }

            # Sort by relevance
            is_relevant = analysis.get('is_relevant', False)
            if is_relevant:
                relevant_results.append(result)
            else:
                not_relevant_results.append(result)

            # Display results
            logger.info("\n--- Analysis Results ---")
            logger.info(f"Relevant: {is_relevant}")
            logger.info(f"Reasoning: {analysis.get('relevance_reasoning', 'N/A')}")

            if is_relevant:
                logger.info(f"Summary: {analysis.get('summary', 'N/A')}")
                logger.info(f"Status: {analysis.get('bill_status', 'N/A')}")
                logger.info(f"Type: {analysis.get('legislation_type', 'N/A')}")
                logger.info(f"Categories: {', '.join(analysis.get('categories', []))}")
                logger.info(f"Tags: {', '.join(analysis.get('tags', []))}")

            if analysis.get('key_provisions'):
                logger.info("\nKey Provisions:")
                for j, provision in enumerate(analysis['key_provisions'], 1):
                    logger.info(f"  {j}. {provision}")

            logger.info(f"\nPalliative Care Impact: {analysis.get('palliative_care_impact', 'N/A')}")

            exclusion = analysis.get('exclusion_check', {})
            logger.info(f"\nExclusion Check: {'EXCLUDED' if exclusion.get('is_excluded') else 'INCLUDED'}")
            if exclusion.get('reason'):
                logger.info(f"  Reason: {exclusion['reason']}")

            flags = analysis.get('special_flags', {})
            if any(flags.values()):
                logger.info("\nSpecial Flags:")
                if flags.get('references_regulation'):
                    logger.info(f"  - Regulation: {flags.get('regulation_details')}")
                if flags.get('references_executive_order'):
                    logger.info(f"  - Executive Order: {flags.get('executive_order_details')}")
                if flags.get('references_ballot_measure'):
                    logger.info(f"  - Ballot Measure: {flags.get('ballot_measure_details')}")

        except Exception as e:
            logger.error(f"Error analyzing bill {bill['bill_number']}: {e}")
            not_relevant_results.append({
                'bill': bill,
                'analysis': {'error': str(e), 'is_relevant': False}
            })

    # Save results to separate files
    logger.info(f"\n{'=' * 80}")
    logger.info("7. Saving results...")

    # Save relevant bills
    logger.info(f"   Saving {len(relevant_results)} relevant bills to {RELEVANT_OUTPUT_FILE}...")
    with open(RELEVANT_OUTPUT_FILE, 'w') as f:
        json.dump(relevant_results, f, indent=2)

    # Save not relevant bills
    logger.info(f"   Saving {len(not_relevant_results)} not relevant bills to {NOT_RELEVANT_OUTPUT_FILE}...")
    with open(NOT_RELEVANT_OUTPUT_FILE, 'w') as f:
        json.dump(not_relevant_results, f, indent=2)

    logger.info(f"   Results saved successfully")

    # Summary
    logger.info(f"\n{'=' * 80}")
    logger.info("Analysis Summary")
    logger.info(f"{'=' * 80}")

    total_analyzed = len(bills_to_process)
    total_relevant = len(relevant_results)
    total_not_relevant = len(not_relevant_results)
    total_errors = sum(1 for r in not_relevant_results if 'error' in r['analysis'])

    logger.info(f"Total bills analyzed: {total_analyzed}")
    logger.info(f"Relevant bills: {total_relevant} ({total_relevant/total_analyzed*100:.1f}%)")
    logger.info(f"Not relevant bills: {total_not_relevant} ({total_not_relevant/total_analyzed*100:.1f}%)")
    logger.info(f"Errors: {total_errors}")

    # Comparison with filter pass
    if not test_mode:
        filter_count = len(filter_relevant_bills)
        logger.info(f"\nFilter Pass Comparison:")
        logger.info(f"  Filter pass identified: {filter_count} potentially relevant bills")
        logger.info(f"  Analysis pass confirmed: {total_relevant} relevant bills")
        if filter_count > 0:
            logger.info(f"  Precision improvement: {(total_relevant/filter_count)*100:.1f}% confirmation rate")

    # Category distribution
    all_categories = []
    for result in relevant_results:
        if 'error' not in result['analysis']:
            all_categories.extend(result['analysis'].get('categories', []))

    if all_categories:
        logger.info(f"\nCategory Distribution (Relevant Bills Only):")
        from collections import Counter
        category_counts = Counter(all_categories)
        for category, count in category_counts.most_common():
            logger.info(f"  {category}: {count}")

    logger.info(f"\n{'=' * 80}")
    logger.info("Analysis Complete!")
    logger.info(f"{'=' * 80}")
    if test_mode:
        logger.info("To process all bills, run without TEST_MODE or set: export TEST_MODE=false")


if __name__ == '__main__':
    main()
