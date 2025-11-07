#!/usr/bin/env python3
"""
LegiScan Pipeline CLI Tool
Convenient Python wrapper for running the pipeline in Docker
"""

import subprocess
import sys
import argparse
from pathlib import Path
import json

# ANSI colors
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color


def info(msg):
    print(f"{BLUE}ℹ {msg}{NC}")


def success(msg):
    print(f"{GREEN}✓ {msg}{NC}")


def warning(msg):
    print(f"{YELLOW}⚠ {msg}{NC}")


def error(msg):
    print(f"{RED}✗ {msg}{NC}")


def run_docker_cmd(cmd, env=None, show_output=True):
    """Run a Docker Compose exec command"""
    if isinstance(cmd, str):
        full_cmd = ['docker-compose', 'exec']
        if env:
            for key, value in env.items():
                full_cmd.extend(['-e', f'{key}={value}'])
        full_cmd.extend(['legiscan-pipeline', 'bash', '-c', cmd])
    else:
        full_cmd = ['docker-compose', 'exec', 'legiscan-pipeline'] + cmd

    if show_output:
        result = subprocess.run(full_cmd)
        return result.returncode == 0
    else:
        result = subprocess.run(full_cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr


def check_docker():
    """Check if Docker is running"""
    try:
        subprocess.run(['docker', 'info'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        error("Docker is not running. Please start Docker Desktop.")
        return False


def check_containers():
    """Check if containers are running, start if not"""
    result = subprocess.run(['docker-compose', 'ps'],
                          capture_output=True, text=True)
    if 'Up' not in result.stdout:
        warning("Containers not running. Starting...")
        subprocess.run(['docker-compose', 'up', '-d'])
        import time
        time.sleep(2)


def cmd_fetch(args):
    """Fetch bills from LegiScan"""
    if not check_docker():
        return 1
    check_containers()

    info("Fetching bills from LegiScan...")
    state = args.state or 'CT'
    year = args.year or 2025

    cmd = f'python scripts/fetch_legiscan_bills.py --state {state} --year {year}'
    if run_docker_cmd(cmd):
        success(f"Bills fetched for {state} {year} to data/raw/")
        return 0
    return 1


def cmd_filter(args):
    """Run filter pass"""
    if not check_docker():
        return 1
    check_containers()

    info("Running filter pass...")
    env = {}
    if args.test:
        info("TEST MODE: Processing 5 bills only")
        env = {'TEST_MODE': 'true', 'TEST_COUNT': str(args.test_count or 5)}

    cmd = 'cd scripts && python run_filter_pass.py'
    if run_docker_cmd(cmd, env=env):
        success("Filter results saved to data/filtered/")
        return 0
    return 1


def cmd_analyze(args):
    """Run analysis pass"""
    if not check_docker():
        return 1
    check_containers()

    info("Running analysis pass...")
    env = {}
    if args.test:
        info("TEST MODE")
        env = {'TEST_MODE': 'true', 'TEST_COUNT': str(args.test_count or 5)}

    if args.direct and args.filter_file:
        cmd = f'cd scripts && python run_direct_analysis.py {args.filter_file}'
    else:
        cmd = 'cd scripts && python run_analysis_pass.py'

    if run_docker_cmd(cmd, env=env):
        success("Analysis results saved to data/analyzed/")
        return 0
    return 1


def cmd_run(args):
    """Run full pipeline"""
    info("Running full pipeline...")

    # Fetch
    if cmd_fetch(args) != 0:
        return 1

    # Filter
    if cmd_filter(args) != 0:
        return 1

    # Analyze
    if cmd_analyze(args) != 0:
        return 1

    success("✓✓✓ Full pipeline complete!")
    cmd_results(args)
    return 0


def cmd_shell(args):
    """Open shell in container"""
    if not check_docker():
        return 1
    check_containers()

    info("Opening shell in container...")
    subprocess.run(['docker-compose', 'exec', 'legiscan-pipeline', 'bash'])
    return 0


def cmd_logs(args):
    """Show container logs"""
    if not check_docker():
        return 1

    info("Showing logs (Ctrl+C to exit)...")
    subprocess.run(['docker-compose', 'logs', '-f', '--tail=50', 'legiscan-pipeline'])
    return 0


def cmd_status(args):
    """Show container status"""
    if not check_docker():
        return 1

    info("Container status:")
    subprocess.run(['docker-compose', 'ps'])
    return 0


def cmd_results(args):
    """Show analysis results summary"""
    if not check_docker():
        return 1
    check_containers()

    info("Analysis Results Summary:")

    script = """
import json, sys
from pathlib import Path

analyzed_dir = Path('data/analyzed')
if not analyzed_dir.exists():
    print('No analysis results found')
    sys.exit(0)

files = list(analyzed_dir.glob('*_relevant.json'))
if not files:
    print('No relevant bills found')
    sys.exit(0)

total = 0
for f in files:
    with open(f) as fh:
        bills = json.load(fh)
        count = len(bills)
        total += count
        print(f'{f.name}: {count} relevant bills')

print(f'\\nTotal: {total} relevant bills across all files')
"""

    run_docker_cmd(['python', '-c', script])
    return 0


def cmd_view(args):
    """View detailed analysis results"""
    if not check_docker():
        return 1
    check_containers()

    script = """
import json
from pathlib import Path

f = Path('data/analyzed/analysis_results_relevant.json')
if not f.exists():
    print('No analysis results found. Run: python pipeline.py analyze')
    exit(1)

with open(f) as fh:
    bills = json.load(fh)
    print(f'Total relevant bills: {len(bills)}\\n')

    if bills:
        for i, bill in enumerate(bills[:3], 1):
            print(f'Bill {i}:')
            print(f'  Number: {bill["bill"]["bill_number"]}')
            print(f'  Title: {bill["bill"]["title"][:80]}...')
            print(f'  Categories: {bill["analysis"]["categories"]}')
            print(f'  Status: {bill["analysis"].get("bill_status", "Unknown")}')
            print()

        if len(bills) > 3:
            print(f'... and {len(bills) - 3} more bills')
"""

    run_docker_cmd(['python', '-c', script])
    return 0


def cmd_clean(args):
    """Clean data directories"""
    if not args.yes:
        warning("This will delete all data files (raw, filtered, analyzed)!")
        response = input("Continue? (y/N) ")
        if response.lower() != 'y':
            info("Cancelled")
            return 0

    if not check_docker():
        return 1
    check_containers()

    info("Cleaning data directories...")
    run_docker_cmd('rm -rf data/raw/* data/filtered/* data/analyzed/*')
    success("Data cleaned")
    return 0


def cmd_check(args):
    """Check configuration and API connectivity"""
    if not check_docker():
        return 1
    check_containers()

    info("Checking environment configuration...")

    script = """
import os, sys

errors = []
provider = os.getenv('LLM_PROVIDER', 'portkey')
print(f'LLM Provider: {provider}')

# Check LegiScan
if not os.getenv('LEGISCAN_API_KEY'):
    errors.append('LEGISCAN_API_KEY not set')

# Check LLM
if provider == 'portkey':
    if not os.getenv('PORTKEY_API_KEY'):
        errors.append('PORTKEY_API_KEY not set')
elif provider == 'azure':
    if not os.getenv('AZURE_OPENAI_API_KEY'):
        errors.append('AZURE_OPENAI_API_KEY not set')
    if not os.getenv('AZURE_OPENAI_ENDPOINT'):
        errors.append('AZURE_OPENAI_ENDPOINT not set')
    if not os.getenv('AZURE_OPENAI_DEPLOYMENT'):
        errors.append('AZURE_OPENAI_DEPLOYMENT not set')

if errors:
    print('\\n✗ Configuration errors:')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('\\n✓ Environment configured correctly')
"""

    if run_docker_cmd(['python', '-c', script]):
        success("Configuration check complete")
        return 0
    return 1


def main():
    parser = argparse.ArgumentParser(
        description='LegiScan Pipeline CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python pipeline.py fetch                    # Fetch bills
  python pipeline.py filter                   # Run filter pass
  python pipeline.py analyze                  # Run analysis pass
  python pipeline.py run                      # Run full pipeline
  python pipeline.py run --test               # Quick test (5 bills)
  python pipeline.py results                  # View results
  python pipeline.py shell                    # Open container shell
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch bills from LegiScan')
    fetch_parser.add_argument('--state', help='State code (default: CT)')
    fetch_parser.add_argument('--year', type=int, help='Year (default: 2025)')

    # Filter command
    filter_parser = subparsers.add_parser('filter', help='Run filter pass')
    filter_parser.add_argument('--test', action='store_true', help='Test mode (5 bills)')
    filter_parser.add_argument('--test-count', type=int, help='Number of test bills (default: 5)')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run analysis pass')
    analyze_parser.add_argument('--test', action='store_true', help='Test mode')
    analyze_parser.add_argument('--test-count', type=int, help='Number of test bills')
    analyze_parser.add_argument('--direct', action='store_true', help='Run direct analysis')
    analyze_parser.add_argument('--filter-file', help='Filter results file for direct analysis')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run full pipeline')
    run_parser.add_argument('--test', action='store_true', help='Test mode (5 bills)')
    run_parser.add_argument('--test-count', type=int, help='Number of test bills')
    run_parser.add_argument('--state', help='State code (default: CT)')
    run_parser.add_argument('--year', type=int, help='Year (default: 2025)')

    # Other commands
    subparsers.add_parser('shell', help='Open bash shell in container')
    subparsers.add_parser('logs', help='Show container logs')
    subparsers.add_parser('status', help='Show container status')
    subparsers.add_parser('results', help='Show analysis results summary')
    subparsers.add_parser('view', help='View detailed analysis results')

    clean_parser = subparsers.add_parser('clean', help='Clean data directories')
    clean_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')

    subparsers.add_parser('check', help='Check configuration and API connectivity')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Command mapping
    commands = {
        'fetch': cmd_fetch,
        'filter': cmd_filter,
        'analyze': cmd_analyze,
        'run': cmd_run,
        'shell': cmd_shell,
        'logs': cmd_logs,
        'status': cmd_status,
        'results': cmd_results,
        'view': cmd_view,
        'clean': cmd_clean,
        'check': cmd_check,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        error(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
