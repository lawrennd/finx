#!/usr/bin/env python3

import os
import re
import yaml
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

from finx.entities import EntityManager

# Configure logging
def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    log_file = Path('tax_assistant.log')
    
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

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

class FinancialDocumentManager:
    def __init__(self, base_path=None, tax_year_path=None, config_file=None, private_config_file=None, directory_mapping_file=None, entities_file=None, verbose=False, config=None):
        """Initialize the tax document checker.
        
        Args:
            base_path: Path to the root directory containing all tax documents
            tax_year_path: Path to the specific tax year directory to check
            config_file: Path to the base configuration file
            private_config_file: Path to the private configuration file
            directory_mapping_file: Path to the directory mapping configuration file
            entities_file: Path to the entities configuration file
            verbose: Whether to print verbose output
            config: Optional direct configuration dictionary to use instead of loading from files
        """
        self.logger = logging.getLogger('FinancialDocumentManager')
        self.base_path = Path(base_path) if base_path else None
        self.tax_year_path = Path(tax_year_path) if tax_year_path else None
        self.verbose = verbose
        
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug(f"Initializing FinancialDocumentManager with base_path: {self.base_path}")
        
        # If direct config is provided, use it instead of loading from files
        if config is not None:
            self.base_config = {}
            self.private_config = {}
            self.config = config
            self.directory_mapping = {}
        else:
            # Search for config files in multiple locations
            def find_config_file(filename, explicit_path=None):
                if explicit_path and os.path.exists(explicit_path):
                    if self.verbose:
                        self.logger.debug(f"Found {filename} at explicit path: {explicit_path}")
                    return explicit_path
                
                # Try current working directory
                cwd_path = Path.cwd() / filename
                if cwd_path.exists():
                    if self.verbose:
                        self.logger.debug(f"Found {filename} in current working directory: {cwd_path}")
                    return str(cwd_path)
                
                # Try base directory
                if self.base_path:
                    base_dir_path = self.base_path / filename
                    if base_dir_path.exists():
                        if self.verbose:
                            self.logger.debug(f"Found {filename} in base directory: {base_dir_path}")
                        return str(base_dir_path)
                
                # Try code directory as fallback
                code_path = Path(__file__).parent.parent / filename
                if code_path.exists():
                    if self.verbose:
                        self.logger.debug(f"Found {filename} in code directory")
                    return str(code_path)
                
                if self.verbose:
                    self.logger.warning(f"Could not find {filename}")
                
                # Return a default path in the base directory if no file is found
                default_path = self.base_path / filename if self.base_path else Path(filename)
                return str(default_path)
            
            # Find config files in order of precedence
            self.config_file = find_config_file('finx_base.yml', config_file)
            self.private_config_file = find_config_file('finx_private.yml', private_config_file)
            self.directory_mapping_file = find_config_file('directory_mapping.yml', directory_mapping_file)
            self.entities_file = find_config_file('finx_entities.yml', entities_file)
            
            if self.verbose:
                self.logger.info("\nLoading configurations...")
            
            self.base_config = self.load_base_config()
            self.private_config = self.load_private_config()
            self.directory_mapping = self.load_directory_mapping()
            self.config = self.merge_configs()
        
        # Initialize entity manager
        if entities_file or not config:
            self.entity_manager = EntityManager(self.entities_file)
            if self.verbose:
                self.logger.info("\nLoading entities...")
            self.entities = self.entity_manager.load_entities()
        else:
            self.entity_manager = None
            self.entities = []
            
        # Initialize account_dates before flattening config
        self.account_dates = {}
        
        if self.verbose:
            self.logger.info("\nFlattening configuration...")
        self.required_patterns = self.flatten_config()
        
        if self.verbose:
            self.logger.info("\nAnalyzing account dates...")
        self.account_dates = self.analyze_account_dates()
        
        if self.verbose:
            self.logger.info("Initialization complete")

    def load_base_config(self):
        """Load base configuration from YAML file."""
        if self.config_file:
            try:
                with open(self.config_file, 'r') as f:
                    try:
                        return yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self.logger.error(f"Error parsing base configuration file: {e}")
                        return {}
            except FileNotFoundError:
                self.logger.warning(f"Warning: Base configuration file not found at {self.config_file}")
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
                        self.logger.error(f"Error parsing private configuration file: {e}")
                        return {}
            except FileNotFoundError:
                self.logger.warning(f"Warning: Private configuration file not found at {self.private_config_file}")
                return {}
        return {}

    def load_directory_mapping(self):
        """Load directory mapping from YAML file."""
        if not self.directory_mapping_file:
            if self.verbose:
                self.logger.warning("No directory mapping file specified")
            return {}
            
        try:
            with open(self.directory_mapping_file, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    return config.get('directory_mapping', {})
                except yaml.YAMLError as e:
                    self.logger.error(f"Error parsing directory mapping file: {e}")
                    return {}
        except FileNotFoundError:
            self.logger.warning(f"Warning: Directory mapping file not found at {self.directory_mapping_file}")
            return {}

    def merge_configs(self):
        """Merge base and private configurations."""
        # Start with a deep copy of the base config
        merged = yaml.safe_load(yaml.dump(self.base_config))  # Deep copy
        
        # Define a recursive update function
        def recursive_update(base, update):
            for key, value in update.items():
                # If the value is a list, always extend the existing list
                if isinstance(value, list):
                    if key not in base:
                        base[key] = value
                    elif isinstance(base[key], list):
                        base[key].extend(value)  # Always extend lists
                    else:
                        base[key] = value
                # If the value is a dictionary, update recursively
                elif isinstance(value, dict):
                    if key not in base:
                        base[key] = {}
                    if isinstance(base[key], dict):
                        recursive_update(base[key], value)
                    else:
                        base[key] = value
                # For scalar values, simply update
                else:
                    base[key] = value
            return base
        
        # Apply the private config as an update to the base config
        if self.private_config:
            merged = recursive_update(merged, self.private_config)
        
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
        """Save the configuration back to the YAML file."""
        filename = 'finx_private.yml' if is_private else 'finx_base.yml'
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(config_path, 'w') as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
        self.logger.info(f"Saved configuration to {config_path}")

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
                entity_id = pattern_info['id']
                
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
                        account_dates[entity_id] = {
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
        
        # Update employment dates - handle as a flat list instead of categories
        if 'employment' in updated_config:
            if isinstance(updated_config['employment'], list):
                # Already in the flat structure
                for employer in updated_config['employment']:
                    account_info = self.account_dates.get(employer['id'])
                    if account_info:
                        employer['start_date'] = account_info['start_date']
                        employer['end_date'] = account_info['end_date']
            else:
                # Convert the categorical structure to a flat list
                flat_employment = []
                for category in ['current', 'previous', 'generic']:
                    if category in updated_config['employment']:
                        for employer in updated_config['employment'][category]:
                            # Update dates if available
                            account_info = self.account_dates.get(employer['id'])
                            if account_info:
                                employer['start_date'] = account_info['start_date']
                                employer['end_date'] = account_info['end_date']
                            flat_employment.append(employer)
                
                # Replace the categorical structure with the flat list
                updated_config['employment'] = flat_employment
        
        # Update investment dates
        for region in ['us', 'uk']:
            if region in updated_config.get('investment', {}):
                for investment in updated_config['investment'][region]:
                    account_info = self.account_dates.get(investment['id'])
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
                            # Check if ID is required, don't create one
                            if 'id' not in account_type:
                                self.logger.error(f"Error: Missing ID in account_type for bank {bank['id']}")
                                continue
                            
                            if 'patterns' in account_type:
                                # Get entity name and URL if available
                                entity_id = account_type.get('entity_id', bank.get('entity_id', bank.get('id')))
                                entity_name = None
                                entity_url = None
                                
                                if self.entity_manager:
                                    entity = self.entity_manager.get_entity_by_id(entity_id)
                                    if entity:
                                        entity_name = entity.name
                                        entity_url = entity.url
                                
                                # Combine bank and account_type info
                                combined_info = {
                                    'id': account_type['id'],
                                    'entity_id': entity_id,
                                    'name': f"{entity_name or bank.get('name', 'Bank')} - {account_type.get('name', 'Account')}",
                                    'frequency': account_type.get('frequency', bank.get('frequency', 'monthly')),
                                    'start_date': account_type.get('start_date', bank.get('start_date')),
                                    'end_date': account_type.get('end_date', bank.get('end_date')),
                                    'url': entity_url or bank.get('url')
                                }
                                for pattern in account_type['patterns']:
                                    process_pattern(pattern, combined_info, f'bank_{region}')
                    else:
                        account_info = self.account_dates.get(bank['id'])
                        if account_info:
                            bank['start_date'] = account_info['start_date']
                            bank['end_date'] = account_info['end_date']
        
        # Update additional dates
        if 'additional' in updated_config:
            for item in updated_config['additional']:
                account_info = self.account_dates.get(item['id'])
                if account_info:
                    item['start_date'] = account_info['start_date']
                    item['end_date'] = account_info['end_date']
        
        # Save the updated configuration to the private file only
        self.save_config(updated_config, is_private=True)
        self.logger.info(f"Updated YAML file with dates: {self.private_config_file}")
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
        self.logger.info("Starting to flatten config...")
        patterns = {
            'employment': [],
            'investment_us': [],
            'investment_uk': [],
            'bank_uk': [],
            'bank_us': [],
            'additional': []
        }

        if not self.config:
            self.logger.info("No config found, returning empty patterns")
            return patterns
        
        def process_pattern(pattern, item_info, category_key):
            """Process a pattern and add it to the appropriate category."""
            if pattern is None:
                return
                
            # Build full pattern if it's a dictionary
            if isinstance(pattern, dict):
                full_pattern = self.build_pattern(
                    pattern.get('base', ''),
                    suffix=pattern.get('suffix'),
                    account_type=pattern.get('account_type'),
                    identifiers=pattern.get('identifiers')
                )
            else:
                full_pattern = pattern
                
            # Get default frequency based on category
            default_frequency = 'yearly'  # Default for most categories
            if category_key in ['employment', 'bank_uk', 'bank_us']:
                default_frequency = 'monthly'
               
            # Get document ID - required field
            doc_id = item_info.get('id')
            if not doc_id:
                self.logger.warning(f"Missing document ID for pattern {pattern}, skipping")
                return
            
            # Get entity ID - might be the same as doc_id for backward compatibility
            entity_id = item_info.get('entity_id', doc_id)
                
            # Create the pattern dictionary with all metadata
            pattern_dict = {
                'pattern': full_pattern,
                'id': doc_id,
                'entity_id': entity_id,
                'name': item_info.get('name', ''),
                'frequency': item_info.get('frequency', default_frequency),
                'start_date': pattern.get('start_date', item_info.get('start_date')) if isinstance(pattern, dict) else item_info.get('start_date'),
                'end_date': pattern.get('end_date', item_info.get('end_date')) if isinstance(pattern, dict) else item_info.get('end_date')
            }
            
            # Get URL from entity if available, otherwise from config
            entity_url = self.get_entity_url(entity_id)
            if entity_url:
                pattern_dict['url'] = entity_url
            elif 'url' in item_info:
                pattern_dict['url'] = item_info.get('url')
            
            patterns[category_key].append(pattern_dict)

        # Process employment patterns
        if 'employment' in self.config:
            self.logger.info("Processing employment patterns...")
            if isinstance(self.config['employment'], list):
                # Direct list of employment records (flat structure)
                for employer in self.config['employment']:
                    if 'pattern' in employer:
                        patterns['employment'].append({
                            'pattern': employer['pattern'],
                            'id': employer['id'],
                            'frequency': employer.get('frequency', 'monthly'),
                            'start_date': employer.get('start_date'),
                            'end_date': employer.get('end_date'),
                            'url': employer.get('url')
                        })
                    elif 'patterns' in employer and employer['patterns']:
                        for pattern in employer['patterns']:
                            process_pattern(pattern, employer, 'employment')
            else:
                # Legacy dictionary format with categories - flatten into a unified list
                self.logger.info("Converting categorized employment to flat structure")
                for category in self.config['employment']:
                    self.logger.info(f"Processing employment category: {category}")
                    employers = self.config['employment'][category]
                    if not isinstance(employers, list):
                        employers = [employers]
                        
                    for employer in employers:
                        if 'patterns' in employer and employer['patterns']:
                            for pattern in employer['patterns']:
                                process_pattern(pattern, employer, 'employment')

        # Process investment patterns
        if 'investment' in self.config:
            self.logger.info("Processing investment patterns...")
            for region in ['uk', 'us']:
                if region in self.config['investment']:
                    self.logger.info(f"Processing investment region: {region}")
                    for account in self.config['investment'][region]:
                        if isinstance(account, str):
                            # Handle string patterns directly
                            patterns[f'investment_{region}'].append({
                                'pattern': account,
                                'id': f'investment_{region}',
                                'frequency': 'yearly',
                                'url': None
                            })
                        elif isinstance(account, dict) and 'patterns' in account and account['patterns']:
                            for pattern in account['patterns']:
                                process_pattern(pattern, account, f'investment_{region}')

        # Process bank patterns
        if 'bank' in self.config:
            self.logger.info("Processing bank patterns...")
            for region in ['uk', 'us']:
                if region in self.config['bank']:
                    self.logger.info(f"Processing bank region: {region}")
                    for bank in self.config['bank'][region]:
                        if isinstance(bank, str):
                            # Handle string patterns directly
                            patterns[f'bank_{region}'].append({
                                'pattern': bank,
                                'id': f'bank_{region}',
                                'frequency': 'monthly',
                                'url': None
                            })
                        elif isinstance(bank, dict):
                            # Process account types if present
                            account_types = bank.get('account_types')
                            if account_types is not None:
                                for account_type in account_types:
                                    # Check for missing ID and raise error
                                    if 'id' not in account_type:
                                        self.logger.error(f"Error: Missing ID in account_type for bank {bank['id']}")
                                        continue
                                    
                                    if 'patterns' in account_type:
                                        # Get entity name and URL if available
                                        entity_id = account_type.get('entity_id', bank.get('entity_id', bank.get('id')))
                                        entity_name = None
                                        entity_url = None
                                        
                                        if self.entity_manager:
                                            entity = self.entity_manager.get_entity_by_id(entity_id)
                                            if entity:
                                                entity_name = entity.name
                                                entity_url = entity.url
                                        
                                        # Combine bank and account_type info
                                        combined_info = {
                                            'id': account_type['id'],
                                            'entity_id': entity_id,
                                            'name': f"{entity_name or bank.get('name', 'Bank')} - {account_type.get('name', 'Account')}",
                                            'frequency': account_type.get('frequency', bank.get('frequency', 'monthly')),
                                            'start_date': account_type.get('start_date', bank.get('start_date')),
                                            'end_date': account_type.get('end_date', bank.get('end_date')),
                                            'url': entity_url or bank.get('url')
                                        }
                                        for pattern in account_type['patterns']:
                                            process_pattern(pattern, combined_info, f'bank_{region}')
                            # Process patterns directly on bank if present
                            elif 'patterns' in bank:
                                for pattern in bank['patterns']:
                                    process_pattern(pattern, bank, f'bank_{region}')

        # Process additional patterns
        if 'additional' in self.config:
            self.logger.info("Processing additional patterns...")
            if isinstance(self.config['additional'], dict) and 'patterns' in self.config['additional']:
                patterns_dict = self.config['additional']['patterns']
                for name, pattern_info in patterns_dict.items():
                    if isinstance(pattern_info, dict):
                        pattern_info['name'] = name
                        if 'id' not in pattern_info:
                            pattern_info['id'] = name.replace('_', '-')
                        
                        if 'base' in pattern_info:
                            # Create a pattern with the base
                            full_pattern = self.build_pattern(pattern_info['base'])
                            pattern_dict = {
                                'pattern': full_pattern,
                                'id': pattern_info['id'],
                                'name': pattern_info.get('name', ''),
                                'frequency': pattern_info.get('frequency', 'yearly')
                            }
                            patterns['additional'].append(pattern_dict)
                        else:
                            # Use the pattern info directly
                            process_pattern(pattern_info, pattern_info, 'additional')
            elif isinstance(self.config['additional'], list):
                for item in self.config['additional']:
                    if isinstance(item, str):
                        # Handle string patterns directly
                        patterns['additional'].append({
                            'pattern': item,
                            'id': 'additional',
                            'frequency': 'yearly',
                            'url': None
                        })
                    elif isinstance(item, dict) and 'patterns' in item:
                        for pattern in item['patterns']:
                            process_pattern(pattern, item, 'additional')

        self.logger.info("Finished flattening config")
        return patterns

    def get_year_from_path(self, path):
        """Extract year from file path or directory name."""
        year_match = re.search(r'20\d{2}', str(path))
        return year_match.group(0) if year_match else None

    def find_files_matching_pattern(self, pattern, year=None, category=None):
        """Find all files matching a pattern for a specific year in relevant directories."""
        if self.verbose:
            self.logger.debug(f"    Searching for pattern: {pattern}")
            self.logger.debug(f"    Year: {year}")
            self.logger.debug(f"    Category: {category}")
        
        matches = []
        
        # Get relevant directories for this category
        search_dirs = self.directory_mapping.get(category, [])
        
        if self.verbose:
            self.logger.debug(f"    Search directories: {search_dirs}")
        
        # If no specific directories are mapped, search everywhere
        if not search_dirs:
            search_dirs = ['']
        
        for search_dir in search_dirs:
            # Construct the full path to search
            search_path = self.base_path / search_dir
            
            if self.verbose:
                self.logger.debug(f"    Searching in directory: {search_path}")
            
            # Skip if directory doesn't exist
            if not search_path.exists():
                if self.verbose:
                    self.logger.debug(f"    Directory does not exist: {search_path}")
                continue
            
            # Use Path.glob to find all PDF files
            for file_path in search_path.glob('**/*.pdf'):
                if file_path.is_file():
                    # Get the filename only for pattern matching
                    filename = file_path.name
                    if self.verbose:
                        self.logger.debug(f"    Checking file: {filename}")
                    
                    if re.search(pattern, filename):
                        file_year = self.get_year_from_path(file_path)
                        if year is None or file_year == year:
                            if self.verbose:
                                self.logger.debug(f"    Match found: {file_path}")
                            matches.append(str(file_path))
        
        # Sort matches alphabetically (effectively by date since filenames start with date)
        if self.verbose:
            self.logger.debug(f"    Total matches found: {len(matches)}")
        
        return sorted(matches)

    def list_available_years(self):
        """List all available tax years in the base directory."""
        if self.verbose:
            self.logger.info("\nListing available tax years...")
            self.logger.info(f"Base path: {self.base_path}")
        
        years = set()
        
        # If a specific tax year path is provided, use that
        if self.tax_year_path:
            if self.verbose:
                self.logger.debug(f"Using specific tax year path: {self.tax_year_path}")
            try:
                year_match = re.search(r'20\d{2}', str(self.tax_year_path))
                if year_match:
                    years.add(year_match.group())
                    if self.verbose:
                        self.logger.debug(f"Found year: {year_match.group()}")
            except (ValueError, TypeError):
                if self.verbose:
                    self.logger.warning("Error parsing tax year path")
                pass
            return sorted(list(years))
        
        # Otherwise, search all directories
        if self.verbose:
            self.logger.info("Searching all directories for tax years...")
        
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
                                        self.logger.debug(f"Found year {year} in file: {file_path}")
                    except (PermissionError, OSError) as e:
                        self.logger.error(f"Error accessing directory {search_path}: {str(e)}")
                        continue
                else:
                    if self.verbose:
                        self.logger.warning(f"Directory not found: {search_path}")
        
        if self.verbose:
            self.logger.info(f"Total years found: {len(years)}")
            self.logger.info(f"Years: {sorted(list(years))}")
        
        return sorted(list(years))

    def check_year(self, year, list_missing=False):
        """Check documents for a specific tax year.
        
        Args:
            year (str): The tax year to check
            list_missing (bool): If True, generate dummy filenames for missing files
        
        Returns:
            dict: A dictionary containing:
                - Category-to-files mappings
                - 'all_found': A boolean indicating whether all required documents were found
                - 'missing_files': List of dictionaries containing missing file info:
                    - 'path': Path to the missing file
                    - 'name': Name of the document
                    - 'url': URL where the document can be found (if available)
                    - 'frequency': Document frequency
                - 'found_files': List of found files
                - 'errors': List of any errors encountered
        """
        self.logger.info(f"\nChecking documents for tax year {year}")
        self.logger.info("=" * 50 + "\n")
        
        # Initialize results dictionary
        results = {
            'year': year,
            'missing_files': [],
            'found_files': [],
            'errors': [],
            'all_found': True
        }
        
        # Add category mappings
        for category in self.required_patterns.keys():
            results[category] = []
        
        # Check if year directory exists
        year_path = None
        if self.base_path:
            year_path = self.base_path / str(year)
            if not year_path.exists() and list_missing:
                year_path.mkdir(parents=True, exist_ok=True)
        
        # Process each category
        for category, patterns in self.required_patterns.items():
            if patterns:
                self.logger.info(f"\n{category.upper()}:")
                for pattern_info in patterns:
                    pattern = pattern_info['pattern']
                    entity_id = pattern_info['id']
                    frequency = pattern_info.get('frequency', 'yearly')
                    url = pattern_info.get('url')  # Get URL if available
                    
                    # Check date range
                    calendar_year_start = datetime(int(year), 1, 1)
                    calendar_year_end = datetime(int(year), 12, 31)
                    
                    try:
                        start_date = datetime.strptime(pattern_info.get('start_date', '1900-01-01'), '%Y-%m-%d')
                        end_date = datetime.strptime(pattern_info.get('end_date', '9999-12-31'), '%Y-%m-%d')
                        
                        # Skip if completely outside date range
                        if end_date < calendar_year_start or start_date > calendar_year_end:
                            self.logger.info(f"⏭️ Skipping {entity_id} ({frequency}) - not active in {year} (active from {start_date.year} to {end_date.year})")
                            continue
                    except (ValueError, TypeError):
                        if self.verbose:
                            self.logger.warning(f"  Warning: Could not parse dates, proceeding with check")
                    
                    # Find matching files
                    matches = self.find_files_matching_pattern(pattern, year, category)
                    
                    # Add files to results if found
                    if matches:
                        results[category].extend(matches)
                        results['found_files'].extend(matches)
                    else:
                        self.logger.warning(f"✗ No files found for {entity_id} ({frequency})")
                        self.logger.warning(f"  Pattern used: {pattern}")
                        if url:
                            self.logger.info(f"  Document can be found at: {url}")
                        
                        # Generate dummy filename if requested
                        if list_missing:
                            # Get the appropriate directories for this category
                            target_dirs = self.directory_mapping.get(category, [''])
                            
                            # Extract the pattern format without the year
                            pattern_without_year = pattern.replace(str(year), 'YYYY')
                            
                            # Generate dummy filename based on frequency
                            if frequency in ['yearly', 'annual', 'once']:
                                # For yearly files, just use the year without month and day
                                dummy_filename = f"{year}-MM-DD_{entity_id}.pdf"
                                
                                # Create an entry for each target directory
                                for target_dir in target_dirs:
                                    # Create the full path using the target directory
                                    if target_dir:
                                        full_path = self.base_path / target_dir / dummy_filename
                                    else:
                                        full_path = year_path / dummy_filename  # Fallback to year path if no directory mapping
                                        
                                    missing_info = {
                                        'path': str(full_path),
                                        'name': entity_id,
                                        'frequency': frequency,
                                        'category': category,
                                        'url': url
                                    }
                                    results['missing_files'].append(missing_info)
                                    
                                self.logger.info(f"  Generated dummy filename: {dummy_filename}")
                            elif frequency == 'monthly':
                                # For monthly files, include month but omit day
                                for month in range(1, 13):
                                    dummy_filename = f"{year}-{month:02d}-DD_{entity_id}.pdf"
                                    
                                    # Create an entry for each target directory
                                    for target_dir in target_dirs:
                                        # Create the full path using the target directory
                                        if target_dir:
                                            full_path = self.base_path / target_dir / dummy_filename
                                        else:
                                            full_path = year_path / dummy_filename  # Fallback to year path if no directory mapping
                                            
                                        missing_info = {
                                            'path': str(full_path),
                                            'name': entity_id,
                                            'frequency': frequency,
                                            'category': category,
                                            'url': url
                                        }
                                        results['missing_files'].append(missing_info)
                                    
                                    self.logger.info(f"  Generated dummy filename: {dummy_filename}")
                            elif frequency == 'quarterly':
                                # For quarterly files, use Q1, Q2, Q3, Q4
                                for quarter in range(1, 5):
                                    dummy_filename = f"{year}-Q{quarter}-DD_{entity_id}.pdf"
                                    
                                    # Create an entry for each target directory
                                    for target_dir in target_dirs:
                                        # Create the full path using the target directory
                                        if target_dir:
                                            full_path = self.base_path / target_dir / dummy_filename
                                        else:
                                            full_path = year_path / dummy_filename  # Fallback to year path if no directory mapping
                                            
                                        missing_info = {
                                            'path': str(full_path),
                                            'name': entity_id,
                                            'frequency': frequency,
                                            'category': category,
                                            'url': url
                                        }
                                        results['missing_files'].append(missing_info)
                                    
                                    self.logger.info(f"  Generated dummy filename: {dummy_filename}")
                        
                        results['all_found'] = False
                        continue
                    
                    # Validate frequency
                    is_valid, found_count, expected_count = self.validate_frequency(matches, frequency, year, pattern_info)
                    
                    if found_count > 0:
                        if is_valid:
                            self.logger.info(f"✓ Found {found_count} files for {entity_id} ({frequency})")
                        else:
                            self.logger.warning(f"✗ Found {found_count} files for {entity_id} ({frequency}), expected {expected_count}")
                            if url:
                                self.logger.info(f"  Document can be found at: {url}")
                        
                            # Generate dummy filenames for missing documents if requested
                            if list_missing:
                                # Get the appropriate directories for this category
                                target_dirs = self.directory_mapping.get(category, [''])
                                
                                missing_count = expected_count - found_count
                                if frequency == 'monthly':
                                    # Find which months are missing
                                    found_months = set()
                                    for match in matches:
                                        date_match = re.search(r'(\d{4})-(\d{2})', match)
                                        if date_match:
                                            found_months.add(int(date_match.group(2)))
                                    
                                    # Generate filenames for missing months
                                    for month in range(1, 13):
                                        if month not in found_months:
                                            dummy_filename = f"{year}-{month:02d}-DD_{entity_id}.pdf"
                                            
                                            # Create an entry for each target directory
                                            for target_dir in target_dirs:
                                                # Create the full path using the target directory
                                                if target_dir:
                                                    full_path = self.base_path / target_dir / dummy_filename
                                                else:
                                                    full_path = year_path / dummy_filename  # Fallback to year path if no directory mapping
                                                    
                                                missing_info = {
                                                    'path': str(full_path),
                                                    'name': entity_id,
                                                    'frequency': frequency,
                                                    'category': category,
                                                    'url': url
                                                }
                                                results['missing_files'].append(missing_info)
                                            
                                            self.logger.info(f"  Generated dummy filename: {dummy_filename}")
                                
                                elif frequency == 'quarterly':
                                    # Find which quarters are missing
                                    found_quarters = set()
                                    for match in matches:
                                        date_match = re.search(r'(\d{4})-(\d{2})', match)
                                        if date_match:
                                            month = int(date_match.group(2))
                                            quarter = (month - 1) // 3 + 1
                                            found_quarters.add(quarter)
                                    
                                    # Generate filenames for missing quarters
                                    for quarter in range(1, 5):
                                        if quarter not in found_quarters:
                                            dummy_filename = f"{year}-Q{quarter}-DD_{entity_id}.pdf"
                                            
                                            # Create an entry for each target directory
                                            for target_dir in target_dirs:
                                                # Create the full path using the target directory
                                                if target_dir:
                                                    full_path = self.base_path / target_dir / dummy_filename
                                                else:
                                                    full_path = year_path / dummy_filename  # Fallback to year path if no directory mapping
                                                    
                                                missing_info = {
                                                    'path': str(full_path),
                                                    'name': entity_id,
                                                    'frequency': frequency,
                                                    'category': category,
                                                    'url': url
                                                }
                                                results['missing_files'].append(missing_info)
                                            
                                            self.logger.info(f"  Generated dummy filename: {dummy_filename}")
                            
                            results['all_found'] = False
        
        # Print summary of missing files if any
        if results['missing_files']:
            self.logger.warning("\nMISSING OR INCOMPLETE DOCUMENTS SUMMARY:")
            self.logger.warning("=" * 50)
            self.logger.warning("")
            
            # Group missing files by category for better organization
            files_by_category = {}
            for missing_file in sorted(results['missing_files'], key=lambda x: x['path']):
                category = missing_file.get('category', 'unknown')
                if category not in files_by_category:
                    files_by_category[category] = []
                files_by_category[category].append(missing_file)
            
            # Print missing files grouped by category
            for category, files in files_by_category.items():
                target_dirs = self.directory_mapping.get(category, [''])
                if target_dirs and target_dirs[0]:
                    self.logger.warning(f"\nCategory: {category.upper()} - Place in: {', '.join(target_dirs)}")
                else:
                    self.logger.warning(f"\nCategory: {category.upper()}")
                
                for missing_file in files:
                    path = missing_file['path']
                    # Remove base_path from the path to show a relative path
                    if self.base_path and str(path).startswith(str(self.base_path)):
                        relative_path = Path(path).relative_to(self.base_path)
                        self.logger.warning(f"- {relative_path}")
                    else:
                        self.logger.warning(f"- {path}")
                        
                    if 'url' in missing_file and missing_file['url']:
                        self.logger.warning(f"  Can be found at: {missing_file['url']}")
            
            self.logger.warning("")
        
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

    def get_entity_url(self, entity_id):
        """Get the URL for an entity by ID."""
        # Try to find entity in loaded entities
        if self.entity_manager:
            entity = self.entity_manager.get_entity_by_id(entity_id)
            if entity and entity.url:
                return entity.url
                
        # Fall back to config if entity not found or no entity manager
        # Check in employment
        if 'employment' in self.config:
            for employer in self.config['employment']:
                if isinstance(employer, dict):
                    # Check entity_id first, then fall back to id (backwards compatibility)
                    if employer.get('entity_id') == entity_id or employer.get('id') == entity_id:
                        if 'url' in employer:
                            return employer['url']
                    
        # Check in investment
        if 'investment' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['investment']:
                    for item in self.config['investment'][region]:
                        if isinstance(item, dict):
                            # Check entity_id first, then fall back to id
                            if item.get('entity_id') == entity_id or item.get('id') == entity_id:
                                if 'url' in item:
                                    return item['url']
                            
        # Check in bank
        if 'bank' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['bank']:
                    for item in self.config['bank'][region]:
                        if isinstance(item, dict):
                            # Check entity_id first, then fall back to id
                            if item.get('entity_id') == entity_id or item.get('id') == entity_id:
                                if 'url' in item:
                                    return item['url']
                            
        return None

    def get_entity_status(self, start_date=None, end_date=None):
        """
        Determine the status of an entity based on its start and end dates.
        
        Args:
            start_date: Optional string in format 'YYYY-MM-DD'
            end_date: Optional string in format 'YYYY-MM-DD'
            
        Returns:
            str: 'current', 'previous', or 'inactive'
        """
        today = datetime.now().date()
        
        # Parse dates if provided
        parsed_start = None
        parsed_end = None
        
        if start_date:
            try:
                parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid start date format: {start_date}")
        
        if end_date:
            try:
                parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid end date format: {end_date}")
        
        # Determine status based on dates
        if parsed_start and not parsed_end:
            # Has start date but no end date = current
            return 'current'
        elif parsed_start and parsed_end:
            # Has both start and end dates
            if parsed_end < today:
                # End date is in the past = previous
                return 'previous'
            else:
                # End date is in the future = still active but ending
                return 'current'
        else:
            # No dates or only end date without start date
            # Default to inactive
            return 'inactive'

    def validate_entity_references(self):
        """Validate that all entity_id references exist in the entities file."""
        if not self.entity_manager:
            self.logger.warning("No entity manager available for validation")
            return False
            
        entities = self.entity_manager.load_entities()
        if not entities:
            self.logger.warning("No entities loaded for validation")
            return False
            
        entity_ids = {entity.id for entity in entities}
        missing_entities = []
        
        # Check employment
        if 'employment' in self.config:
            for employer in self.config['employment']:
                if isinstance(employer, dict) and 'entity_id' in employer:
                    entity_id = employer['entity_id']
                    if entity_id not in entity_ids:
                        missing_entities.append((entity_id, 'employment', employer.get('id')))
        
        # Check investment
        if 'investment' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['investment']:
                    for item in self.config['investment'][region]:
                        if isinstance(item, dict) and 'entity_id' in item:
                            entity_id = item['entity_id']
                            if entity_id not in entity_ids:
                                missing_entities.append((entity_id, f'investment_{region}', item.get('id')))
        
        # Check bank
        if 'bank' in self.config:
            for region in ['uk', 'us']:
                if region in self.config['bank']:
                    for item in self.config['bank'][region]:
                        if isinstance(item, dict) and 'entity_id' in item:
                            entity_id = item['entity_id']
                            if entity_id not in entity_ids:
                                missing_entities.append((entity_id, f'bank_{region}', item.get('id')))
                                
                        # Check account types
                        if isinstance(item, dict) and 'account_types' in item:
                            for account in item['account_types']:
                                if 'entity_id' in account:
                                    entity_id = account['entity_id']
                                    if entity_id not in entity_ids:
                                        missing_entities.append((entity_id, f'bank_{region}', account.get('id')))
        
        # Check additional
        if 'additional' in self.config:
            if isinstance(self.config['additional'], list):
                for item in self.config['additional']:
                    if isinstance(item, dict) and 'entity_id' in item:
                        entity_id = item['entity_id']
                        if entity_id not in entity_ids:
                            missing_entities.append((entity_id, 'additional', item.get('id')))
        
        if missing_entities:
            self.logger.warning(f"Found {len(missing_entities)} missing entity references:")
            for entity_id, category, doc_id in missing_entities:
                self.logger.warning(f"  - Missing entity '{entity_id}' referenced by {category}/{doc_id}")
            return False
            
        return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check tax documents for a specific year')
    parser.add_argument('--year', type=str, help='Specific year to check (e.g., 2023)')
    parser.add_argument('--update-dates', action='store_true', help='Update YAML with inferred dates')
    parser.add_argument('--list-missing', action='store_true', help='Generate dummy filenames for missing files')
    parser.add_argument('--validate-entities', action='store_true', help='Validate entity ID references')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    args = parser.parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(log_level)
    
    # If verbose is set, override the log level to DEBUG
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Assuming the script is run from the parent directory of the tax folders
    base_path = os.path.dirname(os.path.abspath(__file__))
    checker = FinancialDocumentManager(base_path, verbose=args.verbose)
    
    if args.verbose:
        logger.debug(f"Base path: {base_path}")
        logger.debug(f"Config file: {checker.config_file}")
        logger.debug(f"Private config file: {checker.private_config_file}")
        logger.debug(f"Directory mapping file: {checker.directory_mapping_file}")
    
    if args.validate_entities:
        if args.verbose:
            logger.info("Validating entity references...")
        valid = checker.validate_entity_references()
        if valid:
            logger.info("All entity references are valid")
        else:
            logger.error("Some entity references are invalid. See warnings above.")
        return
    
    if args.update_dates:
        if args.verbose:
            logger.info("Updating YAML file with inferred dates...")
        updated_config = checker.update_yaml_with_dates()
        logger.info("Updated YAML file with inferred dates")
        return
    
    if args.year:
        if args.verbose:
            logger.info(f"Checking documents for year {args.year}")
        checker.check_year(args.year, list_missing=args.list_missing)
    else:
        available_years = checker.list_available_years()
        logger.info(f"Available tax years: {', '.join(available_years)}")
        
        if args.verbose:
            logger.info(f"Checking documents for all available years: {available_years}")
        
        for year in available_years:
            checker.check_year(year, list_missing=args.list_missing)

if __name__ == "__main__":
    main() 