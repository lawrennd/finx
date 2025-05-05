#!/usr/bin/env python3

import sys
import logging
import json
import csv
from enum import Enum
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import typer
import click
import os
import yaml
from .checker import FinancialDocumentManager
from .archive import create_zip_archive
from .entities import EntityManager

# Create Typer app instances
app = typer.Typer(help="Financial management toolkit")
entities_app = typer.Typer(help="Manage financial entities and their contact details")
app.add_typer(entities_app, name="entities")

# Define output format as an Enum for type validation
class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    csv = "csv"

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

# Tax command group
tax_app = typer.Typer(help="Tax document management")
app.add_typer(tax_app, name="tax")

@tax_app.command("status")
def tax_status(
    year: Optional[str] = typer.Option(None, help="Specific tax year to check (e.g., 2023)"),
    base_path: str = typer.Option(".", help="Base path for tax documents (default: current directory)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
    log_file: Optional[str] = typer.Option(None, help="Path to log file (default: finx.log)"),
    config_file: Optional[str] = typer.Option(None, help="Path to base configuration file"),
    private_config_file: Optional[str] = typer.Option(None, help="Path to private configuration file"),
    directory_mapping_file: Optional[str] = typer.Option(None, help="Path to directory mapping file"),
    entities_file: Optional[str] = typer.Option(None, help="Path to entities file")
):
    """Check tax document status for one or more years."""
    logger = logging.getLogger('finx')
    
    checker = FinancialDocumentManager(
        base_path=base_path,
        config_file=config_file,
        private_config_file=private_config_file,
        directory_mapping_file=directory_mapping_file,
        entities_file=entities_file,
        verbose=verbose
    )
    
    # If a specific year is provided, check only that year
    if year:
        print(f"Checking documents for year {year}")
        results = checker.check_year(year, list_missing=False)
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

@tax_app.command("missing")
def tax_missing(
    year: Optional[str] = typer.Option(None, help="Specific tax year to check (e.g., 2023)"),
    base_path: str = typer.Option(".", help="Base path for tax documents (default: current directory)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
    log_file: Optional[str] = typer.Option(None, help="Path to log file (default: finx.log)"),
    config_file: Optional[str] = typer.Option(None, help="Path to base configuration file"),
    private_config_file: Optional[str] = typer.Option(None, help="Path to private configuration file"),
    directory_mapping_file: Optional[str] = typer.Option(None, help="Path to directory mapping file"),
    entities_file: Optional[str] = typer.Option(None, help="Path to entities file"),
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format for file listing")
):
    """List missing tax documents."""
    logger = logging.getLogger('finx')
    
    checker = FinancialDocumentManager(
        base_path=base_path,
        config_file=config_file,
        private_config_file=private_config_file,
        directory_mapping_file=directory_mapping_file,
        entities_file=entities_file,
        verbose=verbose
    )
    
    # Get years to check
    if year:
        years_to_check = [year]
    else:
        years_to_check = checker.list_available_years()
        if not years_to_check:
            print("No tax years found in the directory.")
            return 0
    
    # Process each year
    for year in years_to_check:
        results = checker.check_year(year, list_missing=True)
        
        # Format and display results based on requested format
        if format == OutputFormat.json:
            print(json.dumps(results, indent=2))
        elif format == OutputFormat.csv:
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

@tax_app.command("zip")
def tax_zip(
    year: Optional[str] = typer.Option(None, help="Specific tax year to archive (e.g., 2023)"),
    base_path: str = typer.Option(".", help="Base path for tax documents (default: current directory)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
    log_file: Optional[str] = typer.Option(None, help="Path to log file (default: finx.log)"),
    config_file: Optional[str] = typer.Option(None, help="Path to base configuration file"),
    private_config_file: Optional[str] = typer.Option(None, help="Path to private configuration file"),
    directory_mapping_file: Optional[str] = typer.Option(None, help="Path to directory mapping file"),
    dummy: bool = typer.Option(False, help="Run in dummy mode without creating zip"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Path where to save the zip file"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password for the zip file")
):
    """Create zip archive of tax documents."""
    logger = logging.getLogger('finx')
    
    # Set default year if not provided
    if not year:
        year = str(datetime.now().year)
    
    success = create_zip_archive(
        year=year,
        dummy=dummy,
        base_path=base_path,
        config_file=config_file,
        private_config_file=private_config_file,
        directory_mapping_file=directory_mapping_file,
        output_path=output_path,
        password=password,
        verbose=verbose
    )
    
    return 0 if success else 1

@tax_app.command("update-dates")
def tax_update_dates(
    year: Optional[str] = typer.Option(None, help="Specific tax year to check (e.g., 2023)"),
    base_path: str = typer.Option(".", help="Base path for tax documents (default: current directory)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
    log_file: Optional[str] = typer.Option(None, help="Path to log file (default: finx.log)"),
    config_file: Optional[str] = typer.Option(None, help="Path to base configuration file"),
    private_config_file: Optional[str] = typer.Option(None, help="Path to private configuration file"),
    directory_mapping_file: Optional[str] = typer.Option(None, help="Path to directory mapping file"),
    entities_file: Optional[str] = typer.Option(None, help="Path to entities file")
):
    """Update the configuration with inferred dates."""
    logger = logging.getLogger('finx')
    
    checker = FinancialDocumentManager(
        base_path=base_path,
        config_file=config_file,
        private_config_file=private_config_file,
        directory_mapping_file=directory_mapping_file,
        entities_file=entities_file,
        verbose=verbose
    )
    
    logger.info("Updating YAML with inferred dates...")
    checker.update_yaml_with_dates()
    logger.info("YAML updated successfully!")
    
    return 0

# Placeholder commands for future development
@app.command("invest")
def invest(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging")
):
    """Investment tracking (planned)."""
    typer.echo("Investment tracking functionality is planned but not yet implemented.")
    typer.echo("This feature will be available in a future version.")
    return 0

@app.command("networth")
def networth(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging")
):
    """Net worth tracking (planned)."""
    typer.echo("Net worth tracking functionality is planned but not yet implemented.")
    typer.echo("This feature will be available in a future version.")
    return 0

@app.command("budget")
def budget(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging")
):
    """Budget management (planned)."""
    typer.echo("Budget management functionality is planned but not yet implemented.")
    typer.echo("This feature will be available in a future version.")
    return 0

@app.command("estate")
def estate(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging")
):
    """Estate planning (planned)."""
    typer.echo("Estate planning functionality is planned but not yet implemented.")
    typer.echo("This feature will be available in a future version.")
    return 0

@app.command("savings")
def savings(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging")
):
    """Savings goals tracking (planned)."""
    typer.echo("Savings goals functionality is planned but not yet implemented.")
    typer.echo("This feature will be available in a future version.")
    return 0

# Entities commands
@entities_app.command("list")
def entities_list(
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter entities by type"),
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format (text, json, csv)"),
    entities_file: Optional[str] = typer.Option(None, help="Path to entities file (default: finx_entities.yml in current directory)")
):
    """List all entities, optionally filtered by type."""
    # Use the specified file or default to finx_entities.yml in the current directory
    if entities_file:
        yaml_path = Path(entities_file)
    else:
        yaml_path = Path(os.getcwd()) / "finx_entities.yml"
    
    manager = EntityManager(yaml_path)
    entities = manager.list_entities(type)
    
    if not entities:
        typer.echo("No entities found.")
        return
    
    # Handle different output formats
    if format == OutputFormat.json:
        typer.echo(json.dumps([entity.to_dict() for entity in entities], indent=2))
    elif format == OutputFormat.csv:
        if entities:
            # Convert nested structures to flat format for CSV
            flat_entities = []
            for entity in entities:
                flat_entity = {
                    'name': entity.name,
                    'type': entity.type.value,
                    'contact_email': entity.contact.get('email', ''),
                    'contact_primary': entity.contact.get('primary', '')
                }
                flat_entities.append(flat_entity)
                
            writer = csv.DictWriter(sys.stdout, fieldnames=flat_entities[0].keys())
            writer.writeheader()
            writer.writerows(flat_entities)
        else:
            # Write empty CSV with default headers
            writer = csv.DictWriter(sys.stdout, fieldnames=['name', 'type', 'contact_email', 'contact_primary'])
            writer.writeheader()
    else:
        # Text format (default)
        for entity in entities:
            typer.echo("\n" + manager.format_entity(entity))
            typer.echo("-" * 50)

@entities_app.command("check")
def entities_check(
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format (text, json, csv)"),
    entities_file: Optional[str] = typer.Option(None, help="Path to entities file (default: finx_entities.yml in current directory)")
):
    """Check for entities mentioned in config files but not in entities list."""
    # Use the specified file or default to finx_entities.yml in the current directory
    if entities_file:
        yaml_path = Path(entities_file)
    else:
        yaml_path = Path(os.getcwd()) / "finx_entities.yml"
    
    manager = EntityManager(yaml_path)
    
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
    
    # Format output based on selected format
    if format == OutputFormat.json:
        result = {
            "missing_entities": missing,
            "total_missing": len(missing)
        }
        typer.echo(json.dumps(result, indent=2))
    elif format == OutputFormat.csv:
        if missing:
            writer = csv.writer(sys.stdout)
            writer.writerow(["entity_name"])
            for name in missing:
                writer.writerow([name])
        else:
            writer = csv.writer(sys.stdout)
            writer.writerow(["entity_name"])
    else:
        # Text format (default)
        if missing:
            typer.echo("The following entities are mentioned in config files but not in the entities list:")
            for name in missing:
                typer.echo(f"  - {name}")
        else:
            typer.echo("All entities mentioned in config files are listed in the entities database.")

@entities_app.command("validate")
def entities_validate(
    format: OutputFormat = typer.Option(OutputFormat.text, help="Output format (text, json, csv)"),
    entities_file: Optional[str] = typer.Option(None, help="Path to entities file (default: finx_entities.yml in current directory)"),
    base_path: str = typer.Option(".", help="Base path for tax documents (default: current directory)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output for debugging"),
    config_file: Optional[str] = typer.Option(None, help="Path to base configuration file"),
    private_config_file: Optional[str] = typer.Option(None, help="Path to private configuration file"),
    directory_mapping_file: Optional[str] = typer.Option(None, help="Path to directory mapping file")
):
    """Validate entity ID references in the configuration files."""
    logger = logging.getLogger('finx')
    
    checker = FinancialDocumentManager(
        base_path=base_path,
        config_file=config_file,
        private_config_file=private_config_file,
        directory_mapping_file=directory_mapping_file,
        entities_file=entities_file,
        verbose=verbose
    )
    
    print("Validating entity references...")
    valid = checker.validate_entity_references()
    missing_entities = []
    
    # For JSON and CSV output formats, we need to collect missing entities
    if format != OutputFormat.text and not valid:
        entities = checker.entity_manager.load_entities()
        entity_ids = {entity.id for entity in entities}
        
        # Similar to validate_entity_references but returns missing entities
        # Check employment
        if 'employment' in checker.config:
            for employer in checker.config['employment']:
                if isinstance(employer, dict) and 'entity_id' in employer:
                    entity_id = employer['entity_id']
                    if entity_id not in entity_ids:
                        missing_entities.append({
                            'entity_id': entity_id, 
                            'category': 'employment', 
                            'doc_id': employer.get('id')
                        })
        
        # Check investment
        if 'investment' in checker.config:
            for region in ['uk', 'us']:
                if region in checker.config['investment']:
                    for item in checker.config['investment'][region]:
                        if isinstance(item, dict) and 'entity_id' in item:
                            entity_id = item['entity_id']
                            if entity_id not in entity_ids:
                                missing_entities.append({
                                    'entity_id': entity_id, 
                                    'category': f'investment_{region}', 
                                    'doc_id': item.get('id')
                                })
        
        # Check bank
        if 'bank' in checker.config:
            for region in ['uk', 'us']:
                if region in checker.config['bank']:
                    for item in checker.config['bank'][region]:
                        if isinstance(item, dict) and 'entity_id' in item:
                            entity_id = item['entity_id']
                            if entity_id not in entity_ids:
                                missing_entities.append({
                                    'entity_id': entity_id, 
                                    'category': f'bank_{region}', 
                                    'doc_id': item.get('id')
                                })
                                
                        # Check account types
                        if isinstance(item, dict) and 'account_types' in item:
                            for account in item['account_types']:
                                if 'entity_id' in account:
                                    entity_id = account['entity_id']
                                    if entity_id not in entity_ids:
                                        missing_entities.append({
                                            'entity_id': entity_id, 
                                            'category': f'bank_{region}', 
                                            'doc_id': account.get('id')
                                        })
        
        # Check additional
        if 'additional' in checker.config:
            if isinstance(checker.config['additional'], list):
                for item in checker.config['additional']:
                    if isinstance(item, dict) and 'entity_id' in item:
                        entity_id = item['entity_id']
                        if entity_id not in entity_ids:
                            missing_entities.append({
                                'entity_id': entity_id, 
                                'category': 'additional', 
                                'doc_id': item.get('id')
                            })
    
    # Format output based on selected format
    if format == OutputFormat.json:
        result = {
            "valid": valid,
            "missing_entities": missing_entities,
            "total_missing": len(missing_entities)
        }
        typer.echo(json.dumps(result, indent=2))
    elif format == OutputFormat.csv:
        if missing_entities:
            writer = csv.DictWriter(sys.stdout, fieldnames=['entity_id', 'category', 'doc_id'])
            writer.writeheader()
            writer.writerows(missing_entities)
        else:
            # Write empty CSV with headers
            writer = csv.DictWriter(sys.stdout, fieldnames=['entity_id', 'category', 'doc_id'])
            writer.writeheader()
    else:
        # Text format (default)
        if valid:
            print("All entity references are valid")
        else:
            print("Some entity references are invalid. See warnings above.")
    
    return 0 if valid else 1

def extract_entity_names(config):
    """Extract potential entity names from a configuration dictionary."""
    entity_names = []
    
    # Extract from employment
    if 'employment' in config:
        # Check if employment is a list (flat structure)
        if isinstance(config['employment'], list):
            for employer in config['employment']:
                if isinstance(employer, dict) and 'name' in employer:
                    entity_names.append(employer['name'])
                elif isinstance(employer, str):
                    entity_names.append(employer)
        else:
            # Handle the legacy categorical structure
            for category, value in config['employment'].items():
                if isinstance(value, list):
                    for employer in value:
                        if isinstance(employer, dict) and 'name' in employer:
                            entity_names.append(employer['name'])
                        elif isinstance(employer, str):
                            entity_names.append(employer)
                elif isinstance(value, dict) and 'name' in value:
                    entity_names.append(value['name'])
                elif isinstance(value, str):
                    entity_names.append(value)
    
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

def main():
    """Main entry point for the CLI."""
    try:
        return app()
    except Exception as e:
        error_message = f"Error: {str(e)}"
        sys.stderr.write(f"{error_message}\n")
        logger = logging.getLogger('finx')
        logger.error(f"Error executing command: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 