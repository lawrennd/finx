#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from .checker import TaxDocumentChecker

def main():
    parser = argparse.ArgumentParser(description='Check tax documents against configured patterns')
    parser.add_argument('--year', type=str, help='Specific tax year to check (e.g., 2023)')
    parser.add_argument('--update-dates', action='store_true', help='Update YAML with inferred dates')
    parser.add_argument('--base-path', type=str, default='.', help='Base path for tax documents')
    
    args = parser.parse_args()
    
    # Initialize checker
    checker = TaxDocumentChecker(args.base_path)
    
    # Update dates if requested
    if args.update_dates:
        print("Updating YAML with inferred dates...")
        checker.update_yaml_with_dates()
        print("YAML updated successfully!")
        return 0
    
    # Check specific year if provided
    if args.year:
        if not checker.check_year(args.year):
            return 1
        return 0
    
    # Otherwise, check all available years
    years = checker.list_available_years()
    if not years:
        print("No tax years found in the directory!")
        return 1
    
    all_found = True
    for year in years:
        if not checker.check_year(year):
            all_found = False
    
    return 0 if all_found else 1

if __name__ == '__main__':
    sys.exit(main()) 