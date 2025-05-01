#!/usr/bin/env python3

import argparse
import sys
import logging
import json
import csv
from pathlib import Path
from datetime import datetime
from .checker import TaxDocumentChecker
from .archive import create_zip_archive
import click
import os
import yaml
from .entities import EntityManager

def setup_logging(log_file=None, verbose=False, console_output=False):
    """Set up logging configuration."""
    if log_file is None:
        log_file = 'finx.log'
    
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
                'path': missing_file['path'],
                'name': missing_file['name'],
                'frequency': missing_file['frequency'],
                'url': missing_file.get('url'),
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
        else:
            # Write empty CSV with default headers
            writer = csv.DictWriter(sys.stdout, fieldnames=['year', 'path', 'status'])
            writer.writeheader()
    else:  # text format
        if not years_to_check:
            print("\nNo tax years found in the directory.")
            return
        
        if not files:
            print("\nNo missing files found.")
            return
        
        current_year = None
        
        for file in files:
            # Print year header if it's a new year
            if file['year'] != current_year:
                current_year = file['year']
                print(f"\nYear: {current_year}")
            
            # Print file info
            print(f"    {Path(file['path']).name}")

def tax_status_command(args):
    """Command to check tax document status for one or more years."""
    logger = logging.getLogger('finx')
    
    checker = TaxDocumentChecker(
        base_path=args.base_path,
        config_file=args.config_file,
        private_config_file=args.private_config_file,
        directory_mapping_file=args.directory_mapping_file,
        entities_file=args.entities_file,
        verbose=args.verbose
    )
    
    # If a specific year is provided, check only that year
    if args.year:
        print(f"Checking documents for year {args.year}")
        results = checker.check_year(args.year, list_missing=False)
        return 0 if results['all_found'] else 1
    
    # Otherwise, check all available years
    years = checker.list_available_years()
    if not years:
        logger.warning("No tax years found in the directory.")
        return 0
    
    print(f"Available tax years: {', '.join(years)}")
    all_complete = True
    
    for year in years:
        print(f"Checking documents for year {year}")
        results = checker.check_year(year, list_missing=False)
        if not results['all_found']:
            all_complete = False
    
    return 0 if all_complete else 1

def tax_missing_command(args):
    """Command to list missing tax documents."""
    logger = logging.getLogger('finx')
    
    checker = TaxDocumentChecker(
        base_path=args.base_path,
        config_file=args.config_file,
        private_config_file=args.private_config_file,
        directory_mapping_file=args.directory_mapping_file,
        entities_file=args.entities_file,
        verbose=args.verbose
    )
    
    # Get years to check
    if args.year:
        years_to_check = [args.year]
    else:
        years_to_check = checker.list_available_years()
        if not years_to_check:
            print("No tax years found in the directory.")
            return 0
    
    # Process each year
    for year in years_to_check:
        results = checker.check_year(year, list_missing=True)
        
        # Format and display results based on requested format
        if args.format == 'json':
            print(json.dumps(results, indent=2))
        elif args.format == 'csv':
            if results['missing_files']:
                writer = csv.DictWriter(sys.stdout, fieldnames=['year', 'path', 'name', 'frequency', 'url'])
                writer.writeheader()
                for missing in results['missing_files']:
                    writer.writerow({
                        'year': year,
                        'path': missing['path'],
                        'name': missing['name'],
                        'frequency': missing['frequency'],
                        'url': missing.get('url', '')
                    })
            else:
                print(f"No missing files for year {year}")
        else:
            # Text format (default)
            if results['missing_files']:
                print(f"\nMissing files for year {year}:")
                for missing in results['missing_files']:
                    print(f"- {missing['path']}")
                    if 'url' in missing and missing['url']:
                        print(f"  Can be found at: {missing['url']}")
            else:
                print(f"No missing files for year {year}")
    
    return 0

def tax_zip_command(args):
    """Command to create a zip archive of tax documents."""
    logger = logging.getLogger('finx')
    
    # Set default year if not provided
    if not args.year:
        args.year = str(datetime.now().year)
    
    success = create_zip_archive(
        year=args.year,
        dummy=args.dummy,
        base_path=args.base_path,
        config_file=args.config_file,
        private_config_file=args.private_config_file,
        directory_mapping_file=args.directory_mapping_file,
        verbose=args.verbose
    )
    
    return 0 if success else 1

def tax_update_dates_command(args):
    """Command to update the configuration with inferred dates."""
    logger = logging.getLogger('finx')
    
    checker = TaxDocumentChecker(
        base_path=args.base_path,
        config_file=args.config_file,
        private_config_file=args.private_config_file,
        directory_mapping_file=args.directory_mapping_file,
        entities_file=args.entities_file,
        verbose=args.verbose
    )
    
    logger.info("Updating YAML with inferred dates...")
    checker.update_yaml_with_dates()
    logger.info("YAML updated successfully!")
    
    return 0

def invest_command(args):
    """Placeholder for investment tracking command."""
    logger = logging.getLogger('finx')
    logger.error("Investment tracking functionality is not yet implemented")
    raise NotImplementedError("Investment tracking functionality is not yet implemented")

def networth_command(args):
    """Placeholder for net worth tracking command."""
    logger = logging.getLogger('finx')
    logger.error("Net worth tracking functionality is not yet implemented")
    raise NotImplementedError("Net worth tracking functionality is not yet implemented")

def budget_command(args):
    """Placeholder for budget management command."""
    logger = logging.getLogger('finx')
    logger.error("Budget management functionality is not yet implemented")
    raise NotImplementedError("Budget management functionality is not yet implemented")

def estate_command(args):
    """Placeholder for estate planning command."""
    logger = logging.getLogger('finx')
    logger.error("Estate planning functionality is not yet implemented")
    raise NotImplementedError("Estate planning functionality is not yet implemented")

def savings_command(args):
    """Placeholder for savings goals command."""
    logger = logging.getLogger('finx')
    logger.error("Savings goals functionality is not yet implemented")
    raise NotImplementedError("Savings goals functionality is not yet implemented")

def setup_tax_parser(subparsers):
    """Set up the parser for the 'tax' command."""
    tax_parser = subparsers.add_parser('tax', help='Tax document management')
    tax_subparsers = tax_parser.add_subparsers(dest='tax_command', help='Tax subcommands')
    
    # Common arguments for all tax subcommands
    tax_common_parser = argparse.ArgumentParser(add_help=False)
    tax_common_parser.add_argument('--year', type=str, help='Specific tax year to check (e.g., 2023)')
    tax_common_parser.add_argument('--base-path', type=str, default='.', help='Base path for tax documents (default: current directory)')
    tax_common_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    tax_common_parser.add_argument('--log-file', type=str, help='Path to log file (default: finx.log)')
    tax_common_parser.add_argument('--config-file', type=str, help='Path to base configuration file')
    tax_common_parser.add_argument('--private-config-file', type=str, help='Path to private configuration file')
    tax_common_parser.add_argument('--directory-mapping-file', type=str, help='Path to directory mapping file')
    tax_common_parser.add_argument('--entities-file', type=str, help='Path to entities file')
    
    # Tax status command
    status_parser = tax_subparsers.add_parser('status', parents=[tax_common_parser], help='Check tax document status')
    status_parser.set_defaults(func=tax_status_command)
    
    # Tax missing command
    missing_parser = tax_subparsers.add_parser('missing', parents=[tax_common_parser], help='List missing tax documents')
    missing_parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text', 
                              help='Output format for file listing (default: text)')
    missing_parser.set_defaults(func=tax_missing_command)
    
    # Tax zip command
    zip_parser = tax_subparsers.add_parser('zip', parents=[tax_common_parser], help='Create zip archive of tax documents')
    zip_parser.add_argument('--dummy', action='store_true', help='Run in dummy mode without creating zip')
    zip_parser.set_defaults(func=tax_zip_command)
    
    # Tax update-dates command
    update_dates_parser = tax_subparsers.add_parser('update-dates', parents=[tax_common_parser], help='Update YAML with inferred dates')
    update_dates_parser.set_defaults(func=tax_update_dates_command)

def setup_invest_parser(subparsers):
    """Set up the parser for the 'invest' command."""
    invest_parser = subparsers.add_parser('invest', help='Investment tracking (planned)')
    invest_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    invest_parser.set_defaults(func=invest_command)

def setup_networth_parser(subparsers):
    """Set up the parser for the 'networth' command."""
    networth_parser = subparsers.add_parser('networth', help='Net worth tracking (planned)')
    networth_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    networth_parser.set_defaults(func=networth_command)

def setup_budget_parser(subparsers):
    """Set up the parser for the 'budget' command."""
    budget_parser = subparsers.add_parser('budget', help='Budget management (planned)')
    budget_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    budget_parser.set_defaults(func=budget_command)

def setup_estate_parser(subparsers):
    """Set up the parser for the 'estate' command."""
    estate_parser = subparsers.add_parser('estate', help='Estate planning (planned)')
    estate_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    estate_parser.set_defaults(func=estate_command)

def setup_savings_parser(subparsers):
    """Set up the parser for the 'savings' command."""
    savings_parser = subparsers.add_parser('savings', help='Savings goals tracking (planned)')
    savings_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output for debugging')
    savings_parser.set_defaults(func=savings_command)

def parse_args(args):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Financial management toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check tax documents for all years
  finx tax status
  
  # Check tax documents for a specific year
  finx tax status --year 2023
  
  # List missing tax documents
  finx tax missing
  
  # Create a zip archive of tax documents
  finx tax zip --year 2023
  
  # Update tax document dates in configuration
  finx tax update-dates
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Set up command parsers
    setup_tax_parser(subparsers)
    setup_invest_parser(subparsers)
    setup_networth_parser(subparsers)
    setup_budget_parser(subparsers)
    setup_estate_parser(subparsers)
    setup_savings_parser(subparsers)
    
    return parser.parse_args(args)

def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    # Set up logging
    log_level = logging.DEBUG if parsed_args.verbose else logging.INFO
    logger = setup_logging(None, log_level)
    
    # Check if a command was provided
    if not parsed_args.command:
        print("No command specified. Use --help to see available commands.")
        return 1
    
    # For tax commands, check if a subcommand was provided
    if parsed_args.command == 'tax' and not hasattr(parsed_args, 'func'):
        print("No tax subcommand specified. Use 'finx tax --help' to see available subcommands.")
        return 1
    
    # Execute the function associated with the command
    if hasattr(parsed_args, 'func'):
        try:
            return parsed_args.func(parsed_args)
        except Exception as e:
            error_message = f"Error: {str(e)}"
            sys.stderr.write(f"{error_message}\n")
            logger.error(f"Error executing command: {str(e)}")
            if parsed_args.verbose:
                import traceback
                logger.error(traceback.format_exc())
            return 1
    
    return 0

@click.group()
def entities():
    """Manage financial entities and their contact details."""
    pass

@entities.command()
@click.option('--type', '-t', help='Filter entities by type')
def list(type):
    """List all entities, optionally filtered by type."""
    manager = EntityManager(os.getcwd())
    entities = manager.list_entities(type)
    
    if not entities:
        click.echo("No entities found.")
        return
    
    for entity in entities:
        click.echo("\n" + manager.format_entity(entity))
        click.echo("-" * 50)

@entities.command()
def check():
    """Check for entities mentioned in config files but not in entities list."""
    manager = EntityManager(os.getcwd())
    
    # Load base and private configs
    config_names = []
    
    # Try to find potential entity names in config files
    base_path = Path(os.getcwd()) / "finx_base.yml"
    private_path = Path(os.getcwd()) / "finx_private.yml"
    
    if base_path.exists():
        with open(base_path, 'r') as f:
            base_config = yaml.safe_load(f)
            config_names.extend(extract_entity_names(base_config))
    
    if private_path.exists():
        with open(private_path, 'r') as f:
            private_config = yaml.safe_load(f)
            config_names.extend(extract_entity_names(private_config))
    
    # Deduplicate names
    config_names = list(set(config_names))
    
    # Check for missing entities
    missing = manager.check_missing_entities(config_names)
    
    if missing:
        click.echo("The following entities are mentioned in config files but not in the entities list:")
        for name in missing:
            click.echo(f"  - {name}")
    else:
        click.echo("All entities mentioned in config files are listed in the entities database.")

def extract_entity_names(config):
    """Extract potential entity names from a configuration dictionary."""
    entity_names = []
    
    # Extract from employment
    if 'employment' in config:
        for employer in config['employment']:
            if isinstance(employer, dict) and 'name' in employer:
                entity_names.append(employer['name'])
            elif isinstance(employer, str):
                entity_names.append(employer)
    
    # Extract from investment
    if 'investment' in config:
        for region in ['uk', 'us']:
            if region in config['investment']:
                for item in config['investment'][region]:
                    if isinstance(item, dict) and 'name' in item:
                        entity_names.append(item['name'])
                    elif isinstance(item, str):
                        entity_names.append(item)
    
    # Extract from bank
    if 'bank' in config:
        for region in ['uk', 'us']:
            if region in config['bank']:
                for item in config['bank'][region]:
                    if isinstance(item, dict) and 'name' in item:
                        entity_names.append(item['name'])
                    elif isinstance(item, str):
                        entity_names.append(item)
    
    return entity_names

if __name__ == "__main__":
    sys.exit(main()) 