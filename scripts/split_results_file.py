#!/usr/bin/env python3
"""
Split large results file into smaller chunks for batch processing.

Usage:
    python split_results_file.py <input_file> [--chunk-size 100]

Example:
    python split_results_file.py ../data/filtered/results_masterlist-nomic-top1000-score59.json
"""

import json
import sys
from pathlib import Path
import argparse


def split_results_file(input_file: str, chunk_size: int = 100):
    """
    Split a results file into smaller chunks.

    Args:
        input_file: Path to input JSON file
        chunk_size: Number of bills per chunk (default: 100)
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Load the input file
    print(f"Loading {input_path.name}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate structure
    if 'results' not in data:
        print("Error: Input file must have 'results' array")
        sys.exit(1)

    results = data['results']
    total_bills = len(results)

    print(f"Total bills: {total_bills}")
    print(f"Chunk size: {chunk_size}")

    # Calculate number of chunks
    num_chunks = (total_bills + chunk_size - 1) // chunk_size  # Ceiling division
    print(f"Creating {num_chunks} chunks...")

    # Create base filename without extension
    base_name = input_path.stem
    output_dir = input_path.parent

    # Split into chunks
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min(start_idx + chunk_size, total_bills)
        chunk_results = results[start_idx:end_idx]

        # Create chunk data with same structure
        chunk_data = {
            "total_results": len(chunk_results),
            "results": chunk_results
        }

        # Generate output filename
        chunk_num = i + 1
        output_file = output_dir / f"{base_name}_chunk{chunk_num:02d}.json"

        # Write chunk file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2)

        print(f"  Created {output_file.name} ({len(chunk_results)} bills)")

    print(f"\nSuccessfully split {total_bills} bills into {num_chunks} files")
    print(f"Output location: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Split large results file into smaller chunks for batch processing'
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=100,
        help='Number of bills per chunk (default: 100)'
    )

    args = parser.parse_args()

    split_results_file(args.input_file, args.chunk_size)


if __name__ == '__main__':
    main()
