#!/usr/bin/env python3

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Standard patterns used across all document types
STANDARD_PATTERNS = {
    'date': r'\d{4}-\d{2}-\d{2}',
    'extension': r'\.pdf$'
}

# Expected number of files per year based on frequency
FREQUENCY_EXPECTATIONS = {
    'monthly': 12,
    'quarterly': 4,
    'yearly': 1,
    'annual': 1,
    'once': 1
}

class TaxDocumentChecker:
    def __init__(self, base_path, tax_year_path=None, config_file=None, private_config_file=None, directory_mapping_file=None, verbose=False):
        """Initialize the tax document checker.
        
        Args:
            base_path: Path to the root directory containing all tax documents
            tax_year_path: Path to the specific tax year directory to check
            config_file: Path to the base configuration file
            private_config_file: Path to the private configuration file
            directory_mapping_file: Path to the directory mapping configuration file
            verbose: Whether to print verbose output
        """
        self.base_path = Path(base_path)
        self.tax_year_path = Path(tax_year_path) if tax_year_path else None
        self.verbose = verbose
        
        if self.verbose:
            print(f"Initializing TaxDocumentChecker with base_path: {self.base_path}")
        
        # Search for config files in multiple locations
        def find_config_file(filename, explicit_path=None):
            if explicit_path and os.path.exists(explicit_path):
                if self.verbose:
                    print(f"Found {filename} at explicit path: {explicit_path}")
                return explicit_path
            
            # Try current working directory
            cwd_path = Path.cwd() / filename
            if cwd_path.exists():
                if self.verbose:
                    print(f"Found {filename} in current working directory: {cwd_path}")
                return str(cwd_path)
            
            # Try base directory
            base_dir_path = self.base_path / filename
            if base_dir_path.exists():
                if self.verbose:
                    print(f"Found {filename} in base directory: {base_dir_path}")
                return str(base_dir_path)
            
            # Try code directory as fallback
            code_path = Path(__file__).parent.parent / filename
            if code_path.exists():
                if self.verbose:
                    print(f"Found {filename} in code directory")
                return str(code_path)
            
            if self.verbose:
                print(f"Could not find {filename}")
            return explicit_path  # Return explicit path even if not found, for error messaging
        
        # Find config files in order of precedence
        self.config_file = find_config_file('tax_document_patterns_base.yaml', config_file)
        self.private_config_file = find_config_file('tax_document_patterns_private.yaml', private_config_file)
        self.directory_mapping_file = find_config_file('directory_mapping.yaml', directory_mapping_file)
        
        if self.verbose:
            print("\nLoading configurations...")
        
        self.base_config = self.load_base_config()
        self.private_config = self.load_private_config()
        self.directory_mapping = self.load_directory_mapping()
        self.config = self.merge_configs()
        
        # Initialize account_dates before flattening config
        self.account_dates = {}
        
        if self.verbose:
            print("\nFlattening configuration...")
        self.required_patterns = self.flatten_config()
        
        if self.verbose:
            print("\nAnalyzing account dates...")
        self.account_dates = self.analyze_account_dates()
        
        if self.verbose:
            print("Initialization complete")

    def load_base_config(self):
        """Load base configuration from YAML file."""
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    try:
                        return yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        print(f"Error parsing base configuration file: {e}")
                        return {}
            except FileNotFoundError:
                print(f"Warning: Base configuration file not found at {self.config_file}")
                return {}
        return {}

    def load_private_config(self):
        """Load private configuration from YAML file."""
        if self.private_config_file:
            try:
                with open(self.private_config_file, 'r') as f:
                    try:
                        return yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        print(f"Error parsing private configuration file: {e}")
                        return {}
            except FileNotFoundError:
                print(f"Warning: Private configuration file not found at {self.private_config_file}")
                return {}
        return {}

    def load_directory_mapping(self):
        """Load directory mapping from YAML file."""
        try:
            with open(self.directory_mapping_file, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    return config.get('directory_mapping', {})
                except yaml.YAMLError as e:
                    print(f"Error parsing directory mapping file: {e}")
                    return {}
        except FileNotFoundError:
            print(f"Warning: Directory mapping file not found at {self.directory_mapping_file}")
            return {}

    def merge_configs(self):
        """Merge base and private configurations."""
        # Start with a deep copy of the base config
        merged = yaml.safe_load(yaml.dump(self.base_config))  # Deep copy
        
        # Merge with private patterns
        if self.private_config:
            for category in self.private_config:
                if category not in merged:
                    merged[category] = self.private_config[category]
                else:
                    # Handle categories that are lists (like employment categories)
                    if isinstance(self.private_config[category], list):
                        if isinstance(merged[category], list):
                            merged[category].extend(self.private_config[category])
                        else:
                            merged[category] = self.private_config[category]
                    # Handle categories that are dictionaries (like additional patterns)
                    elif isinstance(self.private_config[category], dict):
                        if not isinstance(merged[category], dict):
                            merged[category] = {}
                        for key, value in self.private_config[category].items():
                            if key not in merged[category]:
                                merged[category][key] = value
                            else:
                                # If both are lists, extend
                                if isinstance(value, list) and isinstance(merged[category][key], list):
                                    merged[category][key].extend(value)
                                # If both are dicts, merge recursively
                                elif isinstance(value, dict) and isinstance(merged[category][key], dict):
                                    for subkey, subvalue in value.items():
                                        if subkey in merged[category][key] and isinstance(subvalue, list):
                                            if isinstance(merged[category][key][subkey], list):
                                                merged[category][key][subkey].extend(subvalue)
                                            else:
                                                merged[category][key][subkey] = subvalue
                                        else:
                                            merged[category][key][subkey] = subvalue
                                # Otherwise, overwrite
                                else:
                                    merged[category][key] = value
        
        return merged

    def save_config(self, config, is_private=True):
        """Save configuration to appropriate YAML file."""
        filename = 'tax_document_patterns_private.yaml' if is_private else 'tax_document_patterns_base.yaml'
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(config_path, 'w') as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)

    def extract_date_from_filename(self, filename):
        """Extract date from filename using the standard date pattern."""
        date_match = re.search(STANDARD_PATTERNS['date'], filename)
        if date_match:
            try:
                return datetime.strptime(date_match.group(0), '%Y-%m-%d')
            except ValueError:
                return None
        return None

    def analyze_account_dates(self):
        """Analyze all files to find the start and end dates for each account."""
        account_dates = defaultdict(lambda: {'start_date': None, 'end_date': None, 'files': []})
        
        # Process each category and its patterns
        for category, patterns in self.required_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                name = pattern_info['name']
                
                # Find all matching files across all years
                matches = self.find_files_matching_pattern(pattern, year=None, category=category)
                
                if matches:
                    # Extract dates from filenames
                    dates = []
                    for file in matches:
                        date = self.extract_date_from_filename(os.path.basename(file))
                        if date:
                            dates.append(date)
                    
                    if dates:
                        start_date = min(dates)
                        end_date = max(dates)
                        account_dates[name] = {
                            'start_date': start_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'files': sorted([os.path.basename(f) for f in matches])
                        }
        
        return account_dates

    def validate_frequency(self, matches, frequency, year):
        """Validate that the number of files matches the expected frequency."""
        if not matches:
            return False, 0, FREQUENCY_EXPECTATIONS.get(frequency, 1)
        
        # Count files for the specific year
        year_files = [f for f in matches if str(year) in f]
        expected_count = FREQUENCY_EXPECTATIONS.get(frequency, 1)
        
        # For unknown frequencies, we expect at least one file
        if frequency not in FREQUENCY_EXPECTATIONS:
            return len(year_files) >= 1, len(year_files), 1
        
        return len(year_files) == expected_count, len(year_files), expected_count

    def check_annual_documents(self, matches, year, annual_document_type):
        """Check for both regular documents and annual summary documents."""
        if not matches:
            return False, 0, 2  # Expect 2 forms: regular and annual summary
        
        # Count files for the specific year
        year_files = [f for f in matches if str(year) in f]
        
        # Check for both regular form and annual summary form
        has_regular = any(annual_document_type.lower() not in os.path.basename(f).lower() for f in year_files)
        has_annual = any(annual_document_type.lower() in os.path.basename(f).lower() for f in year_files)
        
        return has_regular and has_annual, len(year_files), 2

    def update_yaml_with_dates(self):
        """Update the YAML configuration with inferred dates."""
        # Create a deep copy of the private config to modify
        updated_config = yaml.safe_load(yaml.dump(self.private_config))
        
        # Update employment dates
        for category in ['current', 'previous', 'generic']:
            if category in updated_config.get('employment', {}):
                for employer in updated_config['employment'][category]:
                    account_info = self.account_dates.get(employer['name'])
                    if account_info:
                        employer['start_date'] = account_info['start_date']
                        employer['end_date'] = account_info['end_date']
        
        # Update investment dates
        for region in ['us', 'uk']:
            if region in updated_config.get('investment', {}):
                for investment in updated_config['investment'][region]:
                    account_info = self.account_dates.get(investment['name'])
                    if account_info:
                        investment['start_date'] = account_info['start_date']
                        investment['end_date'] = account_info['end_date']
        
        # Update bank dates
        for region in ['uk', 'us']:
            if region in updated_config.get('bank', {}):
                for bank in updated_config['bank'][region]:
                    account_types = bank.get('account_types', [])
                    if account_types:
                        for account_type in account_types:
                            account_name = f"{bank['name']} - {account_type['name']}"
                            account_info = self.account_dates.get(account_name)
                            if account_info:
                                account_type['start_date'] = account_info['start_date']
                                account_type['end_date'] = account_info['end_date']
                    else:
                        account_info = self.account_dates.get(bank['name'])
                        if account_info:
                            bank['start_date'] = account_info['start_date']
                            bank['end_date'] = account_info['end_date']
        
        # Update additional dates
        if 'additional' in updated_config:
            for item in updated_config['additional']:
                account_info = self.account_dates.get(item['name'])
                if account_info:
                    item['start_date'] = account_info['start_date']
                    item['end_date'] = account_info['end_date']
        
        # Save the updated configuration to the private file only
        self.save_config(updated_config, is_private=True)
        return updated_config

    def build_pattern(self, base, suffix=None, account_type=None, identifiers=None):
        """Build a regex pattern from components."""
        date_pattern = STANDARD_PATTERNS['date']
        extension = STANDARD_PATTERNS['extension']
        
        pattern_parts = [date_pattern, base]
        
        # Add identifiers if present
        if identifiers:
            identifier_pattern = '|'.join(identifiers)
            pattern_parts.append(f"(?:{identifier_pattern})")
        
        # Add account type if present
        if account_type:
            pattern_parts.append(account_type)
        
        # Add suffix if present
        if suffix:
            pattern_parts.append(suffix)
        
        # Join all parts with underscore except the extension
        return f"{'_'.join(pattern_parts)}{extension}"

    def flatten_config(self):
        """Flatten the configuration into a list of patterns for each category."""
        patterns = {
            'employment': [],
            'investment_us': [],
            'investment_uk': [],
            'bank_uk': [],
            'bank_us': [],
            'additional': []
        }

        if not self.config:
            return patterns

        # Process employment patterns
        if 'employment' in self.config:
            # Process all employment records regardless of category
            for category in self.config['employment']:
                for employer in self.config['employment'][category]:
                    if 'patterns' in employer and employer['patterns']:
                        for pattern in employer['patterns']:
                            if pattern is not None:
                                if isinstance(pattern, dict):
                                    full_pattern = self.build_pattern(
                                        pattern.get('base', ''),
                                        suffix=pattern.get('suffix'),
                                        identifiers=pattern.get('identifiers')
                                    )
                                else:
                                    full_pattern = pattern
                                
                                # Get start and end dates from account_dates if available
                                start_date = None
                                end_date = None
                                if employer['name'] in self.account_dates:
                                    start_date = self.account_dates[employer['name']]['start_date']
                                    end_date = self.account_dates[employer['name']]['end_date']
                                
                                patterns['employment'].append({
                                    'pattern': full_pattern,
                                    'name': employer['name'],
                                    'frequency': employer['frequency'],
                                    'start_date': start_date,
                                    'end_date': end_date
                                })

        # Process investment patterns
        if 'investment' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['investment']:
                    for account in self.config['investment'][region]:
                        if 'patterns' in account and account['patterns']:
                            for pattern in account['patterns']:
                                if pattern is not None:
                                    if isinstance(pattern, dict):
                                        full_pattern = self.build_pattern(
                                            pattern.get('base', ''),
                                            suffix=pattern.get('suffix'),
                                            account_type=pattern.get('account_type'),
                                            identifiers=pattern.get('identifiers')
                                        )
                                    else:
                                        full_pattern = pattern
                                    patterns[f'investment_{region}'].append({
                                        'pattern': full_pattern,
                                        'name': account['name'],
                                        'frequency': account['frequency']
                                    })

        # Process bank patterns
        if 'bank' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['bank']:
                    for bank in self.config['bank'][region]:
                        if 'patterns' in bank and bank['patterns']:
                            for pattern in bank['patterns']:
                                if pattern is not None:
                                    if isinstance(pattern, dict):
                                        full_pattern = self.build_pattern(
                                            pattern.get('base', ''),
                                            suffix=pattern.get('suffix'),
                                            account_type=pattern.get('account_type'),
                                            identifiers=pattern.get('identifiers')
                                        )
                                    else:
                                        full_pattern = pattern
                                    patterns[f'bank_{region}'].append({
                                        'pattern': full_pattern,
                                        'name': bank['name'],
                                        'frequency': bank.get('frequency', 'monthly')
                                    })

        # Process additional patterns
        if 'additional' in self.config:
            if 'patterns' in self.config['additional']:
                for doc_type, info in self.config['additional']['patterns'].items():
                    if isinstance(info, dict):
                        pattern = info.get('base', '')
                        if pattern:
                            full_pattern = self.build_pattern(pattern)
                            patterns['additional'].append({
                                'pattern': full_pattern,
                                'name': doc_type,
                                'frequency': info.get('frequency', 'yearly')
                            })

        return patterns

    def get_year_from_path(self, path):
        """Extract year from file path or directory name."""
        year_match = re.search(r'20\d{2}', str(path))
        return year_match.group(0) if year_match else None

    def find_files_matching_pattern(self, pattern, year=None, category=None):
        """Find all files matching a pattern for a specific year in relevant directories."""
        if self.verbose:
            print(f"    Searching for pattern: {pattern}")
            print(f"    Year: {year}")
            print(f"    Category: {category}")
        
        matches = []
        
        # Get relevant directories for this category
        search_dirs = self.directory_mapping.get(category, [])
        
        if self.verbose:
            print(f"    Search directories: {search_dirs}")
        
        # If no specific directories are mapped, search everywhere
        if not search_dirs:
            search_dirs = ['']
        
        for search_dir in search_dirs:
            # Construct the full path to search
            search_path = self.base_path / search_dir
            
            if self.verbose:
                print(f"    Searching in directory: {search_path}")
            
            # Skip if directory doesn't exist
            if not search_path.exists():
                if self.verbose:
                    print(f"    Directory does not exist: {search_path}")
                continue
            
            # Use Path.glob to find all PDF files
            for file_path in search_path.glob('**/*.pdf'):
                if file_path.is_file():
                    # Get the filename only for pattern matching
                    filename = file_path.name
                    if self.verbose:
                        print(f"    Checking file: {filename}")
                    
                    if re.search(pattern, filename):
                        file_year = self.get_year_from_path(file_path)
                        if year is None or file_year == year:
                            if self.verbose:
                                print(f"    Match found: {file_path}")
                            matches.append(str(file_path))
        
        # Sort matches alphabetically (effectively by date since filenames start with date)
        if self.verbose:
            print(f"    Total matches found: {len(matches)}")
        
        return sorted(matches)

    def list_available_years(self):
        """List all available tax years in the base directory."""
        if self.verbose:
            print("\nListing available tax years...")
            print(f"Base path: {self.base_path}")
        
        years = set()
        
        # If a specific tax year path is provided, use that
        if self.tax_year_path:
            if self.verbose:
                print(f"Using specific tax year path: {self.tax_year_path}")
            try:
                year_match = re.search(r'20\d{2}', str(self.tax_year_path))
                if year_match:
                    years.add(year_match.group())
                    if self.verbose:
                        print(f"Found year: {year_match.group()}")
            except (ValueError, TypeError):
                if self.verbose:
                    print("Error parsing tax year path")
                pass
            return sorted(list(years))
        
        # Otherwise, search all directories
        if self.verbose:
            print("Searching all directories for tax years...")
        
        # Search in all mapped directories
        for category, dirs in self.directory_mapping.items():
            for search_dir in dirs:
                search_path = self.base_path / search_dir
                if search_path.exists():
                    try:
                        # Search for PDF files in this directory and its subdirectories
                        for file_path in search_path.glob('**/*.pdf'):
                            if file_path.is_file():
                                # Extract year from filename
                                year_match = re.search(r'20\d{2}', file_path.name)
                                if year_match:
                                    year = year_match.group()
                                    years.add(year)
                                    if self.verbose:
                                        print(f"Found year {year} in file: {file_path}")
                    except (PermissionError, OSError) as e:
                        print(f"Error accessing directory {search_path}: {str(e)}")
                        continue
                else:
                    if self.verbose:
                        print(f"Directory not found: {search_path}")
        
        if self.verbose:
            print(f"Total years found: {len(years)}")
            print(f"Years: {sorted(list(years))}")
        
        return sorted(list(years))

    def check_year(self, year):
        """Check tax documents for a specific year."""
        if self.verbose:
            print(f"\nStarting document check for tax year {year}")
            print(f"Base path: {self.base_path}")
            print(f"Using patterns: {self.required_patterns}")
        
        print(f"\nChecking documents for tax year {year}\n{'=' * 50}\n")
        
        # Initialize results dictionary with all categories from required_patterns
        results = {category: [] for category in self.required_patterns.keys()}
        
        # Check each pattern
        for category, patterns in self.required_patterns.items():
            if self.verbose:
                print(f"\nProcessing category: {category}")
            
            print(f"\n{category.upper()}:")
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                name = pattern_info['name']
                frequency = pattern_info['frequency']
                
                if self.verbose:
                    print(f"  Checking pattern for {name} ({frequency})")
                    print(f"  Pattern: {pattern}")
                
                # For employment category, check if the record is current for this year
                if category == 'employment':
                    start_date = pattern_info.get('start_date')
                    end_date = pattern_info.get('end_date')
                    
                    if self.verbose and (start_date or end_date):
                        print(f"  Date range: {start_date} to {end_date}")
                    
                    # Skip if this employment record is not active during this year
                    if start_date and end_date:
                        try:
                            start_year = int(start_date.split('-')[0])
                            end_year = int(end_date.split('-')[0])
                            
                            if int(year) < start_year or int(year) > end_year:
                                if self.verbose:
                                    print(f"  Skipping - outside date range ({start_year} to {end_year})")
                                print(f"⏭️ Skipping {name} ({frequency}) - not active in {year} (active from {start_year} to {end_year})")
                                continue
                        except (ValueError, IndexError):
                            if self.verbose:
                                print("  Warning: Could not parse dates, proceeding with check")
                            # If we can't parse the dates, just proceed with checking the files
                            pass
                
                # Find matching files
                if self.verbose:
                    print(f"  Searching for files matching pattern...")
                matches = self.find_files_matching_pattern(pattern, year, category)
                
                if matches:
                    results[category].extend(matches)
                    if self.verbose:
                        print(f"  Found {len(matches)} matching files")
                    print(f"✓ Found {len(matches)} files for {name} ({frequency})")
                else:
                    if self.verbose:
                        print("  No matching files found")
                    print(f"✗ No files found for {name} ({frequency})")
        
        # Print summary of missing documents
        print("\nMISSING OR INCOMPLETE DOCUMENTS SUMMARY:\n" + "=" * 50 + "\n")
        for category, patterns in self.required_patterns.items():
            missing = []
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                name = pattern_info['name']
                frequency = pattern_info['frequency']
                
                if self.verbose:
                    print(f"  Checking {name} for missing documents...")
                
                matches = self.find_files_matching_pattern(pattern, year, category)
                if not matches:
                    missing.append(f"- {name} ({frequency})")
            
            if missing:
                print(f"\n{category.upper()}:")
                print("\n".join(missing))
        
        if self.verbose:
            print("\nDocument check complete")
            print(f"Results: {results}")
        
        return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check tax documents for a specific year')
    parser.add_argument('--year', type=str, help='Specific year to check (e.g., 2023)')
    parser.add_argument('--update-dates', action='store_true', help='Update YAML with inferred dates')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    # Assuming the script is run from the parent directory of the tax folders
    base_path = os.path.dirname(os.path.abspath(__file__))
    checker = TaxDocumentChecker(base_path, verbose=args.verbose)
    
    if args.verbose:
        print(f"Base path: {base_path}")
        print(f"Config file: {checker.config_file}")
        print(f"Private config file: {checker.private_config_file}")
        print(f"Directory mapping file: {checker.directory_mapping_file}")
    
    if args.update_dates:
        if args.verbose:
            print("Updating YAML file with inferred dates...")
        updated_config = checker.update_yaml_with_dates()
        print("Updated YAML file with inferred dates")
        return
    
    if args.year:
        if args.verbose:
            print(f"Checking documents for year {args.year}")
        checker.check_year(args.year)
    else:
        available_years = checker.list_available_years()
        print(f"Available tax years: {', '.join(available_years)}")
        
        if args.verbose:
            print(f"Checking documents for all available years: {available_years}")
        
        for year in available_years:
            checker.check_year(year)

if __name__ == "__main__":
    main() 