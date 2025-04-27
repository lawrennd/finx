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

# Directory mapping for document types
DIRECTORY_MAPPING = {
    'employment': ['UK-payslips'],
    'investment_us': ['US-investments'],
    'investment_uk': ['UK-investments'],
    'bank_uk': ['UK-savings'],
    'bank_us': ['US-savings'],
    'additional': ['US-tax', 'UK-tax']  # Additional documents can be in either tax directory
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
    def __init__(self, base_path, config_file=None):
        self.base_path = Path(base_path)
        self.config_file = config_file
        self.base_config = self.load_base_config()
        self.private_config = self.load_private_config()
        self.config = self.merge_configs()
        self.required_patterns = self.flatten_config()
        self.account_dates = self.analyze_account_dates()

    def load_base_config(self):
        """Load base configuration from YAML file."""
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    try:
                        return yaml.safe_load(f)
                    except yaml.YAMLError:
                        print(f"Warning: Invalid YAML in configuration file at {self.config_file}")
                        return {}
            except FileNotFoundError:
                print(f"Warning: Configuration file not found at {self.config_file}")
                return {}
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tax_document_patterns_base.yaml')
        try:
            with open(config_path, 'r') as f:
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError:
                    print(f"Warning: Invalid YAML in base configuration file at {config_path}")
                    return {}
        except FileNotFoundError:
            print(f"Warning: Base configuration file not found at {config_path}")
            return {}

    def load_private_config(self):
        """Load private configuration from YAML file."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tax_document_patterns_private.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Private configuration file not found at {config_path}")
            return {}

    def merge_configs(self):
        """Merge base and private configurations."""
        merged = {}
        
        # Start with base patterns
        if self.base_config:
            merged = yaml.safe_load(yaml.dump(self.base_config))  # Deep copy
        
        # Merge with private patterns
        if self.private_config:
            for category in self.private_config:
                if category not in merged:
                    merged[category] = self.private_config[category]
                else:
                    # Merge subcategories
                    for subcategory in self.private_config[category]:
                        if subcategory not in merged[category]:
                            merged[category][subcategory] = self.private_config[category][subcategory]
                        else:
                            # If both configs have patterns, combine them
                            if isinstance(merged[category][subcategory], list):
                                merged[category][subcategory].extend(self.private_config[category][subcategory])
                            elif isinstance(merged[category][subcategory], dict):
                                for key, value in self.private_config[category][subcategory].items():
                                    if key in merged[category][subcategory] and isinstance(value, list):
                                        merged[category][subcategory][key].extend(value)
                                    else:
                                        merged[category][subcategory][key] = value
        
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
        """Convert nested YAML config into flat dictionary of patterns with metadata."""
        patterns = {}
        
        # Initialize empty lists for all categories
        patterns['employment'] = []
        patterns['investment_us'] = []
        patterns['investment_uk'] = []
        patterns['bank_uk'] = []
        patterns['bank_us'] = []
        
        if not self.config:
            return patterns
        
        # Process employment patterns
        if 'employment' in self.config:
            for category in ['current', 'previous', 'generic']:
                if category in self.config['employment']:
                    for employer in self.config['employment'][category]:
                        if not employer.get('patterns'):
                            continue
                        for pattern in employer['patterns']:
                            if pattern is None:
                                continue
                            # Handle both dictionary and string patterns
                            if isinstance(pattern, dict):
                                try:
                                    full_pattern = self.build_pattern(
                                        pattern.get('base', ''),
                                        suffix=pattern.get('suffix'),
                                        account_type=pattern.get('account_type'),
                                        identifiers=pattern.get('identifiers')
                                    )
                                except (KeyError, TypeError):
                                    continue
                            else:
                                full_pattern = pattern
                            patterns['employment'].append({
                                'pattern': full_pattern,
                                'name': employer['name'],
                                'frequency': employer['frequency'],
                                'annual_document_type': employer.get('annual_document_type', 'P60')
                            })
        
        # Process investment patterns
        if 'investment' in self.config:
            for region in ['us', 'uk']:
                if region in self.config['investment']:
                    for account in self.config['investment'][region]:
                        for pattern in account['patterns']:
                            # Handle both dictionary and string patterns
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
        
        # Process bank account patterns
        if 'bank' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['bank']:
                    for account in self.config['bank'][region]:
                        for pattern in account['patterns']:
                            # Handle both dictionary and string patterns
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
                                'name': account['name'],
                                'frequency': account['frequency']
                            })
        
        return patterns

    def get_year_from_path(self, path):
        """Extract year from file path or directory name."""
        year_match = re.search(r'20\d{2}', str(path))
        return year_match.group(0) if year_match else None

    def find_files_matching_pattern(self, pattern, year=None, category=None):
        """Find all files matching a pattern for a specific year in relevant directories."""
        matches = []
        
        # Get relevant directories for this category
        search_dirs = DIRECTORY_MAPPING.get(category, [])
        
        # If no specific directories are mapped, search everywhere
        if not search_dirs:
            search_dirs = ['']
        
        for search_dir in search_dirs:
            # Construct the full path to search
            search_path = Path(self.base_path) / search_dir
            
            # Skip if directory doesn't exist
            if not search_path.exists():
                continue
            
            # Use Path.glob to find all PDF files
            for file_path in search_path.glob('**/*.pdf'):
                if file_path.is_file():
                    # Get the filename only for pattern matching
                    filename = file_path.name
                    if re.search(pattern, filename):
                        file_year = self.get_year_from_path(file_path)
                        if year is None or file_year == year:
                            matches.append(str(file_path))
        
        # Sort matches alphabetically (effectively by date since filenames start with date)
        return sorted(matches)

    def check_year(self, year):
        """Check all required documents for a specific year."""
        print(f"\nChecking documents for tax year {year}")
        print("=" * 50)
        
        all_found = True
        missing_files = defaultdict(list)
        
        # Sort categories alphabetically
        for category in sorted(self.required_patterns.keys()):
            print(f"\n{category.upper()}:")
            # Sort patterns by name for consistent output
            for pattern_info in sorted(self.required_patterns[category], key=lambda x: x['name']):
                pattern = pattern_info['pattern']
                name = pattern_info['name']
                frequency = pattern_info['frequency']
                annual_document_type = pattern_info.get('annual_document_type')
                
                # Skip if account is closed before this year or not started yet
                account_info = self.account_dates.get(name)
                if account_info:
                    try:
                        if account_info.get('end_date'):
                            end_date = datetime.strptime(account_info['end_date'], '%Y-%m-%d')
                            if end_date.year < int(year):
                                print(f"⨯ Account '{name}' closed on {account_info['end_date']}")
                                continue
                        if account_info.get('start_date'):
                            start_date = datetime.strptime(account_info['start_date'], '%Y-%m-%d')
                            if start_date.year > int(year):
                                print(f"⨯ Account '{name}' started on {account_info['start_date']}")
                                continue
                    except ValueError:
                        # Invalid date format, ignore the date check
                        pass
                
                matches = self.find_files_matching_pattern(pattern, year, category)
                
                # Check for annual documents if specified
                if annual_document_type:
                    is_valid, found_count, expected_count = self.check_annual_documents(matches, year, annual_document_type)
                else:
                    is_valid, found_count, expected_count = self.validate_frequency(matches, frequency, year)
                
                if matches:
                    if is_valid:
                        print(f"✓ Found {found_count}/{expected_count} files for {name} ({frequency})")
                    else:
                        print(f"⚠ Found {found_count}/{expected_count} files for {name} ({frequency})")
                        all_found = False
                    for match in matches:
                        print(f"  - {os.path.basename(match)}")
                else:
                    print(f"✗ No files found for {name} ({frequency})")
                    missing_files[category].append({
                        'name': name,
                        'frequency': frequency
                    })
                    all_found = False
        
        if not all_found:
            print("\nMISSING OR INCOMPLETE DOCUMENTS SUMMARY:")
            print("=" * 50)
            # Sort categories alphabetically in summary
            for category in sorted(missing_files.keys()):
                print(f"\n{category.upper()}:")
                # Sort missing items by name
                for item in sorted(missing_files[category], key=lambda x: x['name']):
                    print(f"- {item['name']} ({item['frequency']})")
        
        return all_found

    def list_available_years(self):
        """List all available tax years in the directory."""
        years = set()
        for root, dirs, _ in os.walk(self.base_path):
            for dir_name in dirs:
                year = self.get_year_from_path(dir_name)
                if year:
                    years.add(year)
        return sorted(list(years))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check tax documents for a specific year')
    parser.add_argument('--year', type=str, help='Specific year to check (e.g., 2023)')
    parser.add_argument('--update-dates', action='store_true', help='Update YAML with inferred dates')
    args = parser.parse_args()
    
    # Assuming the script is run from the parent directory of the tax folders
    base_path = os.path.dirname(os.path.abspath(__file__))
    checker = TaxDocumentChecker(base_path)
    
    if args.update_dates:
        updated_config = checker.update_yaml_with_dates()
        print("Updated YAML file with inferred dates")
        return
    
    if args.year:
        checker.check_year(args.year)
    else:
        available_years = checker.list_available_years()
        print(f"Available tax years: {', '.join(available_years)}")
        
        for year in available_years:
            checker.check_year(year)

if __name__ == "__main__":
    main() 