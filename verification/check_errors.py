#!/usr/bin/env python3

import argparse
import re
import sys
import os


def check_log_file(log_file):
    if not os.path.exists(log_file):
        print(f"ERROR: Log file '{log_file}' not found")
        sys.exit(1)

    with open(log_file, 'r') as f:
        content = f.read()

    # Check for $error in the log
    if '$error' in content:
        print(f'ERROR: Found $error in {log_file}')
        print(content)
        sys.exit(1)

    # Check for successful completion message
    success_pattern = r'All \d+ test\(s\) completed successfully!'
    if not re.search(success_pattern, content):
        print(f'ERROR: Expected success message not found in {log_file}')
        print("Looking for pattern: 'All X test(s) completed successfully!'")
        print(content)
        sys.exit(1)

    print(f'Log file {log_file} passed all checks')


def main():
    parser = argparse.ArgumentParser(
        description='Check log file for errors and completion status'
    )
    parser.add_argument('log_file', help='Path to the log file to check')

    args = parser.parse_args()
    check_log_file(args.log_file)


if __name__ == '__main__':
    main()
