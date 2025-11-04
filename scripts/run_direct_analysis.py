#!/usr/bin/env python3
"""
Direct Analysis Script - Analyze pre-filtered bills from any filter format
Supports both AI-filtered and vector similarity-filtered bill data
Fetches full bill text from LegiScan API for comprehensive analysis
"""

import os
import sys
import json
import logging
import re
import subprocess
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_analysis_pass import AIAnalysisPass
from src.format_normalizer import normalize_filter_results, detect_format, get_format_info
from src.storage_provider import StorageProviderFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = PROJECT_ROOT / 'config.json'
DATA_DIR = PROJECT_ROOT / 'data'
ANALYZED_DIR = DATA_DIR / 'analyzed'


def load_config():
    """Load configuration from config.json (optional - uses defaults if not found)"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("Config file not found, using default settings")
        return {}


def extract_state_from_url(url: str) -> str:
    """Extract state code from LegiScan URL (e.g., https://legiscan.com/IN/...)"""
    match = re.search(r'legiscan\.com/([A-Z]{2})/', url)
    return match.group(1).lower() if match else None


def extract_year_from_url(url: str) -> str:
    """Extract year from LegiScan URL"""
    match = re.search(r'/(\d{4})$', url)
    return match.group(1) if match else '2025'


def get_source_bills_file(state: str, year: str) -> Path:
    """Construct source bills file path"""
    return DATA_DIR / 'raw' / f'{state}_bills_{year}.json'


def fetch_bills_if_needed(state: str, year: str, source_file: Path):
    """Fetch bills from LegiScan if source file doesn't exist"""
    if source_file.exists():
        logger.info(f"   Source file exists: {source_file}")
        return

    logger.warning(f"   Source file not found: {source_file}")
    logger.info(f"   Fetching {state.upper()} bills for {year} from LegiScan...")

    # Run fetch_legiscan_bills.py with state and year
    fetch_script = SCRIPT_DIR / 'fetch_legiscan_bills.py'
    result = subprocess.run(
        ['python', str(fetch_script), '--state', state.upper(), '--year', year],
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR)
    )

    if result.returncode != 0:
        logger.error(f"Failed to fetch bills: {result.stderr}")
        raise RuntimeError(f"Could not fetch {state.upper()} bills from LegiScan")

    # Move the fetched file from scripts/ to data/raw/
    fetched_file = SCRIPT_DIR / f"{state.lower()}_bills_{year}.json"
    if fetched_file.exists():
        # Ensure data/raw directory exists
        source_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(fetched_file), str(source_file))
        logger.info(f"   Successfully fetched and moved {state.upper()} bills to {source_file}")
    else:
        raise RuntimeError(f"Fetch script did not create expected file: {fetched_file}")


def load_filter_results(filter_file: Path):
    """Load and normalize filtered bill results from any format"""
    try:
        with open(filter_file, 'r') as f:
            data = json.load(f)

        # Detect and log format information
        format_info = get_format_info(data)
        logger.info(f"Filter file format: {format_info['format']}")
        logger.info(f"Bill count: {format_info['bill_count']}")
        logger.info(f"Has summary: {format_info['has_summary']}")
        logger.info(f"Has similarity scores: {format_info['has_similarity_scores']}")

        # Normalize to common format
        normalized_bills = normalize_filter_results(data)
        logger.info(f"Normalized {len(normalized_bills)} bills to common format")

        return normalized_bills
    except FileNotFoundError:
        logger.error(f"Filter results file not found: {filter_file}")
        raise
    except Exception as e:
        logger.error(f"Error loading filter results: {e}")
        raise


def load_source_bills(source_file: Path):
    """Load source bills to get bill_id"""
    try:
        with open(source_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Source bills file not found: {source_file}")
        raise


def create_bill_lookup(source_bills):
    """Create lookup dict from bill_number to full bill data including bill_id"""
    return {bill['bill_number']: bill for bill in source_bills}


def format_bill_for_analysis(bill):
    """
    Format bill data for analysis prompt.

    Args:
        bill: Normalized dict with bill_number, title, url, reason, extra_metadata

    Returns:
        Formatted string for analysis
    """
    formatted = f"""**Bill Number**: {bill['bill_number']}
**Title**: {bill['title']}
**URL**: {bill['url']}"""

    # Include filter reason (from either format)
    if bill.get('reason'):
        formatted += f"\n**Filter Reason**: {bill['reason']}"

    # Include extra metadata if present
    extra = bill.get('extra_metadata', {})
    if extra:
        formatted += f"\n\n**Additional Metadata**:"
        if extra.get('similarity_score') is not None:
            formatted += f"\n- Similarity Score: {extra['similarity_score']:.4f}"
        if extra.get('distance') is not None:
            formatted += f"\n- Distance: {extra['distance']:.4f}"
        if extra.get('status_date'):
            formatted += f"\n- Status Date: {extra['status_date']}"
        if extra.get('last_action'):
            formatted += f"\n- Last Action: {extra['last_action']}"
        if extra.get('year'):
            formatted += f"\n- Year: {extra['year']}"
        if extra.get('session'):
            formatted += f"\n- Session: {extra['session']}"

    return formatted


def select_test_bills(bills, count=5):
    """
    Select diverse test bills for analysis.

    Args:
        bills: List of normalized bill dictionaries
        count: Number of bills to select

    Returns:
        List of selected bills
    """
    selected = []

    # Priority: Pediatric Hospice
    for bill in bills:
        title_lower = bill['title'].lower()
        reason_lower = bill.get('reason', '').lower()
        if 'pediatric hospice' in title_lower or 'pediatric hospice' in reason_lower:
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
        reason_lower = bill.get('reason', '').lower()
        if bill not in selected and ('pain medication' in reason_lower or 'pain management' in reason_lower):
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
    """Main execution"""
    logger.info("=" * 80)
    logger.info("Direct Analysis Pass - Dual-Format Support")
    logger.info("=" * 80)

    # Parse command line arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python run_direct_analysis.py <filter_results_file.json>")
        logger.info("Example: python run_direct_analysis.py ../data/filtered/filter_results_alan_ct_bills_2025.json")
        sys.exit(1)

    filter_file = Path(sys.argv[1])
    if not filter_file.is_absolute():
        filter_file = SCRIPT_DIR / filter_file

    if not filter_file.exists():
        logger.error(f"Filter file not found: {filter_file}")
        sys.exit(1)

    logger.info(f"Input file: {filter_file}")

    # Determine output file name based on input
    filter_filename = filter_file.stem  # e.g., "filter_results_alan_ct_bills_2025"
    output_prefix = filter_filename.replace('filter_results_', 'analysis_')
    RELEVANT_OUTPUT_FILE = ANALYZED_DIR / f"{output_prefix}_relevant.json"
    NOT_RELEVANT_OUTPUT_FILE = ANALYZED_DIR / f"{output_prefix}_not_relevant.json"

    # Load configuration
    logger.info("\n1. Loading configuration...")
    config = load_config()

    # Check for test mode
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    test_count = int(os.getenv('TEST_COUNT', '5'))

    # Get API key from environment variable
    api_key = os.getenv('PORTKEY_API_KEY')
    if not api_key:
        logger.error("PORTKEY_API_KEY environment variable not set")
        logger.info("Set it with: export PORTKEY_API_KEY='your-key'")
        sys.exit(1)

    # Load and normalize filter results
    logger.info("\n2. Loading and normalizing filter results...")
    normalized_bills = load_filter_results(filter_file)
    logger.info(f"   Loaded {len(normalized_bills)} bills from filter results")

    # Detect state and year from first bill's URL
    logger.info("\n3. Detecting state and year from filter results...")
    first_bill = normalized_bills[0]
    state = extract_state_from_url(first_bill['url'])
    year = extract_year_from_url(first_bill['url'])

    if not state:
        logger.error(f"Could not extract state from URL: {first_bill['url']}")
        sys.exit(1)

    logger.info(f"   Detected state: {state.upper()}, year: {year}")

    # Get source bills file path and fetch if needed
    source_bills_file = get_source_bills_file(state, year)
    fetch_bills_if_needed(state, year, source_bills_file)

    # Load source bills to get bill_id
    logger.info(f"\n4. Loading source bills for bill_id lookup...")
    source_bills = load_source_bills(source_bills_file)
    bill_lookup = create_bill_lookup(source_bills)
    logger.info(f"   Loaded {len(source_bills)} total bills for lookup")

    # Select bills to process
    if test_mode:
        logger.info(f"\n5. TEST MODE: Selecting {test_count} bills from filter results...")
        bills_to_process = select_test_bills(normalized_bills, count=test_count)
        logger.info(f"   Selected {len(bills_to_process)} bills for testing:")
    else:
        logger.info(f"\n5. PRODUCTION MODE: Analyzing all {len(normalized_bills)} filtered bills with full text...")
        bills_to_process = normalized_bills
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
    logger.info("\n6. Initializing AI Analysis Pass...")
    analysis_config = config.get('analysis_pass', {})
    timeout = analysis_config.get('timeout', 90)
    api_delay = analysis_config.get('api_delay', 0.0)

    analyzer = AIAnalysisPass(
        api_key=api_key,
        model=config.get('model', 'gpt-4o-mini'),
        temperature=config.get('temperature', 0.3),
        max_tokens=config.get('max_tokens', 2000),
        timeout=timeout,
        legiscan_api_key=legiscan_api_key,
        api_delay=api_delay
    )

    logger.info(f"   Configuration: model={config.get('model', 'gpt-4o-mini')}, "
                f"timeout={timeout}s, max_tokens={config.get('max_tokens', 2000)}, "
                f"api_delay={api_delay}s")

    # Analyze each bill
    logger.info("\n7. Analyzing bills...")
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

            # Add bill info and extra metadata to results
            result = {
                'bill': {
                    'bill_number': bill['bill_number'],
                    'title': bill['title'],
                    'url': bill['url'],
                    'reason': bill.get('reason')
                },
                'analysis': analysis
            }

            # Include extra metadata if present
            if bill.get('extra_metadata'):
                result['bill']['extra_metadata'] = bill['extra_metadata']

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
                'bill': {
                    'bill_number': bill['bill_number'],
                    'title': bill['title'],
                    'url': bill['url'],
                    'reason': bill.get('reason')
                },
                'analysis': {'error': str(e), 'is_relevant': False}
            })

    # Create output directory if it doesn't exist
    ANALYZED_DIR.mkdir(exist_ok=True)

    # Save results to separate files
    logger.info(f"\n{'=' * 80}")
    logger.info("8. Saving results...")

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
