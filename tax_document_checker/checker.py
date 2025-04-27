#!/usr/bin/env python3

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

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
            
            # Return a default path in the base directory if no file is found
            default_path = self.base_path / filename
            return str(default_path)
        
        # Find config files in order of precedence
        self.config_file = find_config_file('tax_document_patterns_base.yml', config_file)
        self.private_config_file = find_config_file('tax_document_patterns_private.yml', private_config_file)
        self.directory_mapping_file = find_config_file('directory_mapping.yml', directory_mapping_file)
        
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
        if not self.directory_mapping_file:
            if self.verbose:
                print("No directory mapping file specified")
            return {}
            
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
                    # Handle categories that are dictionaries (like investment and bank)
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
        
        # Ensure investment and bank categories have proper structure
        for category in ['investment', 'bank']:
            if category in merged:
                for region in ['uk', 'us']:
                    if region in merged[category]:
                        # Convert string values to list of dictionaries
                        if isinstance(merged[category][region], str):
                            merged[category][region] = [{'name': merged[category][region], 'patterns': []}]
                        # Convert list of strings to list of dictionaries
                        elif isinstance(merged[category][region], list):
                            for i, item in enumerate(merged[category][region]):
                                if isinstance(item, str):
                                    merged[category][region][i] = {'name': item, 'patterns': []}
        
        return merged

    def save_config(self, config, is_private=True):
        """Save configuration to appropriate YAML file."""
        filename = 'tax_document_patterns_private.yml' if is_private else 'tax_document_patterns_base.yml'
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

    def validate_frequency(self, matches, frequency, year, pattern_info=None):
        """Validate that the number of files matches the expected frequency."""
        if not matches:
            return False, 0, FREQUENCY_EXPECTATIONS.get(frequency, 1)
        
        # Count files for the specific year
        year_files = [f for f in matches if str(year) in f]
        
        # If this is a regular statement (monthly/quarterly) and we have an annual_document_type,
        # exclude the annual summary from the count
        if frequency in ['monthly', 'quarterly'] and pattern_info and 'annual_document_type' in pattern_info:
            annual_type = pattern_info['annual_document_type'].lower()
            year_files = [f for f in year_files if annual_type not in os.path.basename(f).lower()]
        
        expected_count = FREQUENCY_EXPECTATIONS.get(frequency, 1)
        
        # For unknown frequencies, we expect at least one file
        if frequency not in FREQUENCY_EXPECTATIONS:
            return len(year_files) >= 1, len(year_files), 1
        
        # Calculate expected count based on date range if available
        if pattern_info and frequency in ['monthly', 'quarterly']:
            try:
                year_start = datetime(int(year), 1, 1)
                year_end = datetime(int(year), 12, 31)
                
                # Get pattern start and end dates
                start_date = datetime.strptime(pattern_info.get('start_date', '1900-01-01'), '%Y-%m-%d')
                end_date = datetime.strptime(pattern_info.get('end_date', '9999-12-31'), '%Y-%m-%d')
                
                # Adjust dates to be within the year
                effective_start = max(year_start, start_date)
                effective_end = min(year_end, end_date)
                
                # Calculate number of months in the period
                if frequency == 'monthly':
                    months = (effective_end.year - effective_start.year) * 12 + effective_end.month - effective_start.month + 1
                    expected_count = max(0, months)
                elif frequency == 'quarterly':
                    months = (effective_end.year - effective_start.year) * 12 + effective_end.month - effective_start.month + 1
                    expected_count = max(0, (months + 2) // 3)  # Round up to nearest quarter
            except (ValueError, TypeError):
                # If there's any error parsing dates, fall back to default expectations
                pass
        
        return len(year_files) == expected_count, len(year_files), expected_count

    def check_annual_documents(self, matches, year, annual_document_type):
        """Check for annual summary documents."""
        if not matches:
            return False, 0, 1  # Expect 1 annual summary
        
        # Count files for the specific year that contain the annual_document_type
        year_files = [f for f in matches if str(year) in f and annual_document_type.lower() in os.path.basename(f).lower()]
        
        return len(year_files) == 1, len(year_files), 1

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
        print("Starting to flatten config...")
        patterns = {
            'employment': [],
            'investment_us': [],
            'investment_uk': [],
            'bank_uk': [],
            'bank_us': [],
            'additional': []
        }

        if not self.config:
            print("No config found, returning empty patterns")
            return patterns

        print("Processing employment patterns...")
        # Process employment patterns
        if 'employment' in self.config:
            # Process all employment records regardless of category
            for category in self.config['employment']:
                print(f"Processing employment category: {category}")
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
                                
                                patterns['employment'].append({
                                    'pattern': full_pattern,
                                    'name': employer['name'],
                                    'frequency': employer['frequency'],
                                    'start_date': employer.get('start_date'),
                                    'end_date': employer.get('end_date')
                                })

        print("Processing investment patterns...")
        # Process investment patterns
        if 'investment' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['investment']:
                    print(f"Processing investment region: {region}")
                    for account in self.config['investment'][region]:
                        if isinstance(account, str):
                            # Handle string patterns directly
                            patterns[f'investment_{region}'].append({
                                'pattern': account,
                                'name': f'investment_{region}',
                                'frequency': 'yearly'  # Default frequency for investments
                            })
                        elif isinstance(account, dict) and 'patterns' in account and account['patterns']:
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
                                        'name': account.get('name', f'investment_{region}'),
                                        'frequency': account.get('frequency', 'yearly'),
                                        'start_date': account.get('start_date'),
                                        'end_date': account.get('end_date')
                                    })

        print("Processing bank patterns...")
        # Process bank patterns
        if 'bank' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['bank']:
                    print(f"Processing bank region: {region}")
                    for bank in self.config['bank'][region]:
                        if isinstance(bank, str):
                            # Handle string patterns directly
                            patterns[f'bank_{region}'].append({
                                'pattern': bank,
                                'name': f'bank_{region}',
                                'frequency': 'monthly'  # Default frequency for bank statements
                            })
                        elif isinstance(bank, dict):
                            print(f"Processing bank: {bank.get('name', 'unknown')}")
                            # Process account types if present
                            account_types = bank.get('account_types')
                            if account_types is not None:
                                for account_type in account_types:
                                    if 'patterns' in account_type:
                                        for pattern in account_type['patterns']:
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
                                                    'name': f"{bank['name']} - {account_type['name']}",
                                                    'frequency': account_type.get('frequency', 'monthly'),
                                                    'start_date': pattern.get('start_date'),
                                                    'end_date': pattern.get('end_date')
                                                })
                            # Process patterns directly on bank if present
                            elif 'patterns' in bank:
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
                                            'name': bank.get('name', f'bank_{region}'),
                                            'frequency': bank.get('frequency', 'monthly'),
                                            'start_date': pattern.get('start_date'),
                                            'end_date': pattern.get('end_date')
                                        })

        print("Processing additional patterns...")
        # Process additional patterns
        if 'additional' in self.config:
            if isinstance(self.config['additional'], dict) and 'patterns' in self.config['additional']:
                patterns_dict = self.config['additional']['patterns']
                for name, pattern_info in patterns_dict.items():
                    if isinstance(pattern_info, dict):
                        full_pattern = self.build_pattern(
                            pattern_info.get('base', ''),
                            suffix=pattern_info.get('suffix'),
                            account_type=pattern_info.get('account_type'),
                            identifiers=pattern_info.get('identifiers')
                        )
                        patterns['additional'].append({
                            'pattern': full_pattern,
                            'name': name,
                            'frequency': pattern_info.get('frequency', 'yearly'),
                            'start_date': pattern_info.get('start_date'),
                            'end_date': pattern_info.get('end_date')
                        })
            elif isinstance(self.config['additional'], list):
                for item in self.config['additional']:
                    if isinstance(item, str):
                        # Handle string patterns directly
                        patterns['additional'].append({
                            'pattern': item,
                            'name': 'additional',
                            'frequency': 'yearly'  # Default frequency for additional documents
                        })
                    elif isinstance(item, dict) and 'patterns' in item:
                        for pattern in item['patterns']:
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
                                patterns['additional'].append({
                                    'pattern': full_pattern,
                                    'name': item.get('name', 'additional'),
                                    'frequency': item.get('frequency', 'yearly'),
                                    'start_date': item.get('start_date'),
                                    'end_date': item.get('end_date')
                                })

        print("Finished flattening config")
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
        """Check documents for a specific tax year."""
        print(f"\nChecking documents for tax year {year}")
        print("=" * 50 + "\n")
        
        # Initialize results dictionary with all categories from required_patterns
        results = {category: [] for category in self.required_patterns.keys()}
        all_found = True
        missing_documents = defaultdict(set)  # Changed to set to avoid duplicates
        
        # Process each category
        for category, patterns in self.required_patterns.items():
            if patterns:
                print(f"\n{category.upper()}:")
                for pattern_info in patterns:
                    pattern = pattern_info['pattern']
                    name = pattern_info['name']
                    frequency = pattern_info.get('frequency', 'yearly')
                    
                    # Check date range
                    calendar_year_start = datetime(int(year), 1, 1)
                    calendar_year_end = datetime(int(year), 12, 31)
                    
                    try:
                        start_date = datetime.strptime(pattern_info.get('start_date', '1900-01-01'), '%Y-%m-%d')
                        end_date = datetime.strptime(pattern_info.get('end_date', '9999-12-31'), '%Y-%m-%d')
                        
                        # Skip if completely outside date range
                        if end_date < calendar_year_start or start_date > calendar_year_end:
                            print(f"⏭️ Skipping {name} ({frequency}) - not active in {year} (active from {start_date.year} to {end_date.year})")
                            continue
                    except (ValueError, TypeError):
                        if self.verbose:
                            print(f"  Warning: Could not parse dates, proceeding with check")
                    
                    # Find matching files
                    matches = self.find_files_matching_pattern(pattern, year, category)
                    
                    # Add files to results if found
                    if matches:
                        results[category].extend(matches)
                    
                    # Validate frequency
                    is_valid, found_count, expected_count = self.validate_frequency(matches, frequency, year, pattern_info)
                    
                    if found_count > 0:
                        if is_valid:
                            print(f"✓ Found {found_count} files for {name} ({frequency})")
                        else:
                            print(f"✗ Found {found_count} files for {name} ({frequency}), expected {expected_count}")
                            # For bank accounts, only add the bank name without account type
                            if category.startswith('bank_'):
                                bank_name = name.split(' - ')[0]  # Get the bank name before the account type
                                missing_documents[category].add(f"- {bank_name} ({frequency})")
                            else:
                                missing_documents[category].add(f"- {name} ({frequency})")
                            all_found = False
                    else:
                        # Only add to missing documents if we're not skipping due to date range
                        if not (pattern_info.get('start_date') and pattern_info.get('end_date')):
                            print(f"✗ No files found for {name} ({frequency})")
                            # For bank accounts, only add the bank name without account type
                            if category.startswith('bank_'):
                                bank_name = name.split(' - ')[0]  # Get the bank name before the account type
                                missing_documents[category].add(f"- {bank_name} ({frequency})")
                            else:
                                missing_documents[category].add(f"- {name} ({frequency})")
                            all_found = False
        
        # Print missing documents summary
        if missing_documents:
            print("\nMISSING OR INCOMPLETE DOCUMENTS SUMMARY:")
            print("=" * 50 + "\n")
            for category, documents in missing_documents.items():
                print(f"\n{category.upper()}:")
                for doc in sorted(documents):  # Sort the documents for consistent output
                    print(doc)
                print()
        
        return results

    def find_config_file(self, filename: str) -> Optional[Path]:
        """Find a configuration file in various locations."""
        # Search order:
        # 1. Explicit path if provided
        # 2. Base directory (where the tax documents are)
        # 3. Current working directory
        # 4. Code directory
        if self.base_path:
            base_path = Path(self.base_path)
            if base_path.exists():
                # First check in base directory
                base_file = base_path / filename
                if base_file.exists():
                    return base_file
                
                # Then check in current working directory
                cwd_file = Path.cwd() / filename
                if cwd_file.exists():
                    return cwd_file
                
                # Finally check in code directory
                code_file = Path(__file__).parent / filename
                if code_file.exists():
                    return code_file
        
        return None

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