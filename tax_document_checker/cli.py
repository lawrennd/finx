#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from .checker import TaxDocumentChecker

def main():
    parser = argparse.ArgumentParser(
        description='Check tax documents against configured patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all available tax years
  tax-document-checker
  
  # Check a specific tax year
  tax-document-checker --year 2023
  
  # Update YAML with inferred dates
  tax-document-checker --update-dates
  
  # Check with verbose output
  tax-document-checker --verbose
  
  # Check documents in a specific directory
  tax-document-checker --base-path /path/to/documents
        """
    )
    parser.add_argument('--year', type=str, help='Specific tax year to check (e.g., 2023)')
    parser.add_argument('--update-dates', action='store_true', help='Update YAML with inferred dates from filenames')
    parser.add_argument('--base-path', type=str, default='.', help='Base path for tax documents (default: current directory)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    
    args = parser.parse_args()
    
    if args.verbose:
        print("Initializing TaxDocumentChecker...")
        print(f"Base path: {args.base_path}")
    
    # Initialize checker
    checker = TaxDocumentChecker(args.base_path, verbose=args.verbose)
    
    # Update dates if requested
    if args.update_dates:
        if args.verbose:
            print("\nUpdating YAML with inferred dates...")
        checker.update_yaml_with_dates()
        if args.verbose:
            print("YAML updated successfully!")
        return 0
    
    # Check specific year if provided
    if args.year:
        if args.verbose:
            print(f"\nChecking documents for year {args.year}...")
        if not checker.check_year(args.year):
            return 1
        return 0
    
    # Otherwise, check all available years
    if args.verbose:
        print("\nListing available tax years...")
    years = checker.list_available_years()
    if not years:
        print("No tax years found in the directory!")
        return 1
    
    if args.verbose:
        print(f"Found {len(years)} tax years: {', '.join(years)}")
        print("\nChecking documents for all available years...")
    
    all_found = True
    for year in years:
        if args.verbose:
            print(f"\nProcessing year {year}...")
        result = checker.check_year(year)
        if not result:
            all_found = False
    
    if args.verbose:
        print("\nDocument check complete!")
        print(f"All documents found: {'Yes' if all_found else 'No'}")
    
    return 0 if all_found else 1

if __name__ == '__main__':
    sys.exit(main()) 