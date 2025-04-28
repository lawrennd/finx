#!/usr/bin/env python3

import argparse
import sys
import logging
import json
import csv
from pathlib import Path
from datetime import datetime
from .checker import TaxDocumentChecker

def setup_logging(log_file=None, verbose=False, console_output=False):
    """Set up logging configuration."""
    if log_file is None:
        log_file = 'tax_document_checker.log'
    
    # Create handlers list starting with file handler
    handlers = [logging.FileHandler(log_file)]
    
    # Add console handler only if console_output is True
    if console_output:
        handlers.append(logging.StreamHandler(sys.stdout))
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)

def list_files(checker, year=None, output_format='text'):
    """List all files found by the checker in the specified format."""
    files = []
    
    # Get all years to check
    years_to_check = [year] if year else checker.list_available_years()
    
    # Collect all files
    for year in years_to_check:
        # Get all patterns from the checker
        for category, patterns in checker.required_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                name = pattern_info['name']
                
                # Find matching files
                matches = checker.find_files_matching_pattern(pattern, year=year, category=category)
                
                for file_path in matches:
                    file_info = {
                        'year': year,
                        'category': category,
                        'name': name,
                        'path': str(file_path),
                        'size': Path(file_path).stat().st_size,
                        'modified': datetime.fromtimestamp(Path(file_path).stat().st_mtime).isoformat()
                    }
                    files.append(file_info)
    
    # Sort files by year, category, and name
    files.sort(key=lambda x: (x['year'], x['category'], x['name']))
    
    # Output in requested format
    if output_format == 'json':
        print(json.dumps(files, indent=2))
    elif output_format == 'csv':
        if files:
            writer = csv.DictWriter(sys.stdout, fieldnames=files[0].keys())
            writer.writeheader()
            writer.writerows(files)
        else:
            # Write empty CSV with default headers
            writer = csv.DictWriter(sys.stdout, fieldnames=['year', 'category', 'name', 'path', 'size', 'modified'])
            writer.writeheader()
    else:  # text format
        if not years_to_check:
            print("\nNo tax years found in the directory.")
            return
        
        if not files:
            print("\nNo files found.")
            return
        
        current_year = None
        current_category = None
        
        for file in files:
            # Print year header if it's a new year
            if file['year'] != current_year:
                current_year = file['year']
                print(f"\nYear: {current_year}")
                current_category = None
            
            # Print category header if it's a new category
            if file['category'] != current_category:
                current_category = file['category']
                print(f"\n  {current_category}:")
            
            # Print file info
            size_mb = file['size'] / (1024 * 1024)  # Convert to MB
            print(f"    {Path(file['path']).name} ({size_mb:.2f} MB)")

def list_missing_files(checker, year=None, output_format='text'):
    """List all missing files in the specified format."""
    files = []
    
    # Get all years to check
    years_to_check = [year] if year else checker.list_available_years()
    
    for year in years_to_check:
        results = checker.check_year(year, list_missing=True)
        for missing_file in results['missing_files']:
            file_info = {
                'year': year,
                'path': missing_file,
                'status': 'missing'
            }
            files.append(file_info)
    
    # Sort files by year and path
    files.sort(key=lambda x: (x['year'], x['path']))
    
    # Output in requested format
    if output_format == 'json':
        print(json.dumps(files, indent=2))
    elif output_format == 'csv':
        if files:
            writer = csv.DictWriter(sys.stdout, fieldnames=files[0].keys())
            writer.writeheader()
            writer.writerows(files)
    else:  # text format
        current_year = None
        
        for file in files:
            # Print year header if it's a new year
            if file['year'] != current_year:
                current_year = file['year']
                print(f"\nYear: {current_year}")
            
            # Print file info
            print(f"    {Path(file['path']).name}")

def main():
    parser = argparse.ArgumentParser(
        description='Check tax documents against configured patterns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all files found (default behavior)
  tax-document-checker
  
  # List files in JSON format
  tax-document-checker --format json
  
  # List files in CSV format
  tax-document-checker --format csv
  
  # List files for a specific year
  tax-document-checker --year 2023
  
  # Check compliance without listing files
  tax-document-checker --no-list
  
  # List missing files
  tax-document-checker --list-missing
  
  # List missing files for a specific year
  tax-document-checker --year 2023 --list-missing
  
  # Update YAML with inferred dates
  tax-document-checker --update-dates
  
  # Check with verbose output
  tax-document-checker --verbose
        """
    )
    parser.add_argument('--year', type=str, help='Specific tax year to check (e.g., 2023)')
    parser.add_argument('--update-dates', action='store_true', help='Update YAML with inferred dates from filenames')
    parser.add_argument('--base-path', type=str, default='.', help='Base path for tax documents (default: current directory)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    parser.add_argument('--log-file', type=str, help='Path to log file (default: tax_document_checker.log)')
    parser.add_argument('--console-output', action='store_true', help='Enable logging output to console')
    parser.add_argument('--no-list', action='store_true', help='Skip file listing and only check compliance')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text', 
                      help='Output format for file listing (default: text)')
    parser.add_argument('--list-missing', action='store_true', 
                      help='List missing files')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_file, args.verbose, args.console_output)
    
    logger.info("Initializing TaxDocumentChecker...")
    logger.debug(f"Base path: {args.base_path}")
    
    # Initialize checker
    checker = TaxDocumentChecker(args.base_path, verbose=args.verbose)
    
    # Update dates if requested
    if args.update_dates:
        logger.info("Updating YAML with inferred dates...")
        checker.update_yaml_with_dates()
        logger.info("YAML updated successfully!")
        return 0
    
    # List missing files if requested
    if args.list_missing:
        list_missing_files(checker, args.year, args.format)
        return 0
    
    # Check specific year if provided and --no-list is set
    if args.no_list:
        if args.year:
            logger.info(f"Checking documents for year {args.year}...")
            results = checker.check_year(args.year, list_missing=False)
            if not results['all_found']:
                return 1
            return 0
        
        # Otherwise, check all available years
        logger.info("Listing available tax years...")
        years = checker.list_available_years()
        if not years:
            logger.error("No tax years found in the directory!")
            return 1
        
        logger.info(f"Found {len(years)} tax years: {', '.join(years)}")
        logger.info("Checking documents for all available years...")
        
        all_found = True
        for year in years:
            logger.info(f"Processing year {year}...")
            results = checker.check_year(year, list_missing=False)
            if not results['all_found']:
                all_found = False
        
        logger.info("Document check complete!")
        logger.info(f"All documents found: {'Yes' if all_found else 'No'}")
        
        return 0 if all_found else 1
    
    # List found files (default behavior)
    list_files(checker, args.year, args.format)
    return 0

if __name__ == '__main__':
    sys.exit(main()) 