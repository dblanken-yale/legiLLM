#!/usr/bin/env python3
"""
Analyze statistics from analyzed bill JSON files.

This script reads analyzed JSON files and provides statistics including:
- Total number of bills
- Highest similarity score with bill ID
- Lowest similarity score with bill ID
- Average similarity score
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


def analyze_bill_file(file_path: str) -> Optional[Dict]:
    """
    Analyze a single JSON file containing analyzed bills.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing statistics, or None if file couldn't be processed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None

    if not isinstance(data, list):
        print(f"Error: Expected a list of bills, got {type(data)}")
        return None

    if len(data) == 0:
        return {
            'total_bills': 0,
            'total_with_scores': 0,
            'highest_score': None,
            'lowest_score': None,
            'average_score': None,
            'file': file_path
        }

    # Extract scores and bill information
    bills_with_scores = []
    for bill_data in data:
        # Navigate to the similarity score
        try:
            bill_info = bill_data.get('bill', {})
            extra_metadata = bill_info.get('extra_metadata', {})
            similarity_score = extra_metadata.get('similarity_score')

            if similarity_score is not None:
                bills_with_scores.append({
                    'bill_id': extra_metadata.get('bill_id'),
                    'bill_number': bill_info.get('bill_number'),
                    'title': bill_info.get('title'),
                    'similarity_score': similarity_score
                })
        except (KeyError, AttributeError) as e:
            # Skip bills without proper structure
            continue

    if len(bills_with_scores) == 0:
        print(f"Warning: No bills with similarity scores found in {file_path}")
        return {
            'total_bills': len(data),
            'total_with_scores': 0,
            'highest_score': None,
            'lowest_score': None,
            'average_score': None,
            'file': file_path
        }

    # Calculate statistics
    highest = max(bills_with_scores, key=lambda x: x['similarity_score'])
    lowest = min(bills_with_scores, key=lambda x: x['similarity_score'])
    average = sum(b['similarity_score'] for b in bills_with_scores) / len(bills_with_scores)

    return {
        'total_bills': len(data),
        'total_with_scores': len(bills_with_scores),
        'highest_score': {
            'bill_id': highest['bill_id'],
            'bill_number': highest['bill_number'],
            'title': highest['title'],
            'score': highest['similarity_score']
        },
        'lowest_score': {
            'bill_id': lowest['bill_id'],
            'bill_number': lowest['bill_number'],
            'title': lowest['title'],
            'score': lowest['similarity_score']
        },
        'average_score': average,
        'file': file_path
    }


def print_statistics(stats: Dict) -> None:
    """
    Print statistics in a formatted way.

    Args:
        stats: Statistics dictionary from analyze_bill_file
    """
    print(f"\n{'='*80}")
    print(f"Analysis Results for: {Path(stats['file']).name}")
    print(f"{'='*80}")

    print(f"\nTotal Bills: {stats['total_bills']}")

    if stats['total_with_scores']:
        print(f"Bills with Similarity Scores: {stats['total_with_scores']}")

    if stats['highest_score']:
        print(f"\nHighest Similarity Score:")
        print(f"  Bill ID: {stats['highest_score']['bill_id']}")
        print(f"  Bill Number: {stats['highest_score']['bill_number']}")
        print(f"  Score: {stats['highest_score']['score']:.4f}")
        print(f"  Title: {stats['highest_score']['title'][:100]}...")

    if stats['lowest_score']:
        print(f"\nLowest Similarity Score:")
        print(f"  Bill ID: {stats['lowest_score']['bill_id']}")
        print(f"  Bill Number: {stats['lowest_score']['bill_number']}")
        print(f"  Score: {stats['lowest_score']['score']:.4f}")
        print(f"  Title: {stats['lowest_score']['title'][:100]}...")

    if stats['average_score'] is not None:
        print(f"\nAverage Similarity Score: {stats['average_score']:.4f}")

    print(f"\n{'='*80}\n")


def main():
    """Main function to run the analysis."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_bill_stats.py <path_to_analyzed_json_file>")
        print("\nExample:")
        print("  python analyze_bill_stats.py ../data/analyzed/analysis_alan_ct_bills_2025_relevant.json")
        sys.exit(1)

    file_path = sys.argv[1]

    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File does not exist: {file_path}")
        sys.exit(1)

    # Analyze the file
    stats = analyze_bill_file(file_path)

    if stats is None:
        sys.exit(1)

    # Print results
    print_statistics(stats)

    # Save to JSON file in data/stats directory
    # Get the project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    stats_dir = project_root / 'data' / 'stats'

    # Create stats directory if it doesn't exist
    stats_dir.mkdir(parents=True, exist_ok=True)

    # Save stats file
    output_file = stats_dir / f"{Path(file_path).stem}_stats.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    print(f"Statistics saved to: {output_file}")


if __name__ == '__main__':
    main()
