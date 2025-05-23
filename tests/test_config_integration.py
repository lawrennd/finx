import pytest
import os
import yaml
import tempfile
import shutil
from pathlib import Path
from finx.checker import FinancialDocumentManager
import argparse

class TestConfigIntegration:
    """Integration tests that verify configuration files match documentation."""
    
    def setup_method(self):
        """Set up the test environment."""
        # Find configuration files
        self.base_path = Path(os.path.dirname(os.path.dirname(__file__)))
        self.base_config_file = self.base_path / "finx_base.yml"
        self.dummy_config_file = self.base_path / "finx_dummy.yml"
        self.directory_mapping_file = self.base_path / "directory_mapping.yml"
        
        # Load configuration files
        with open(self.base_config_file, 'r') as f:
            self.base_config = yaml.safe_load(f)
        
        with open(self.dummy_config_file, 'r') as f:
            self.dummy_config = yaml.safe_load(f)
        
        with open(self.directory_mapping_file, 'r') as f:
            self.directory_mapping = yaml.safe_load(f)
            
        # Initialize checker with configurations
        self.checker = FinancialDocumentManager(
            base_path=self.base_path, 
            config_file=self.base_config_file,
            private_config_file=self.dummy_config_file,
            directory_mapping_file=self.directory_mapping_file
        )
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_files(self):
        """Create test files and directories based on configuration."""
        # Set up directory structure according to directory_mapping
        mapping = self.directory_mapping['directory_mapping']
        
        # Create directories
        for category, paths in mapping.items():
            for path in paths:
                os.makedirs(os.path.join(self.temp_dir, path, "2023"), exist_ok=True)
        
        # Create sample files based on patterns in dummy config
        # Employment documents
        for employer in self.dummy_config['employment']:
            if 'patterns' in employer:
                for pattern_info in employer['patterns']:
                    base = pattern_info['base']
                    for month in range(1, 13):
                        date = f"2023-{month:02d}-01"
                        filename = f"{date}_{base}.pdf"
                        sample_file = os.path.join(self.temp_dir, "payslips", "2023", filename)
                        with open(sample_file, 'w') as f:
                            f.write(f"Sample payslip for {base} on {date}")
        
        # Investment documents (US)
        for investment in self.dummy_config['investment']['us']:
            if 'patterns' in investment:
                for pattern_info in investment['patterns']:
                    base = pattern_info['base']
                    date = "2023-12-31"
                    filename = f"{date}_{base}.pdf"
                    sample_file = os.path.join(self.temp_dir, "investments/us", "2023", filename)
                    with open(sample_file, 'w') as f:
                        f.write(f"Sample US investment document for {base} on {date}")
        
        # Investment documents (UK)
        for investment in self.dummy_config['investment']['uk']:
            if 'patterns' in investment:
                for pattern_info in investment['patterns']:
                    base = pattern_info['base']
                    date = "2023-12-31"
                    filename = f"{date}_{base}.pdf"
                    sample_file = os.path.join(self.temp_dir, "investments/uk", "2023", filename)
                    with open(sample_file, 'w') as f:
                        f.write(f"Sample UK investment document for {base} on {date}")
        
        # Bank documents (UK)
        for bank in self.dummy_config['bank']['uk']:
            if 'account_types' in bank:
                for account in bank['account_types']:
                    for pattern_info in account['patterns']:
                        base = pattern_info['base']
                        identifiers = pattern_info.get('identifiers', [])
                        for identifier in identifiers if identifiers else [""]:
                            # Use identifier as suffix if it exists
                            suffix = f"_{identifier}" if identifier else ""
                            for month in range(1, 13):
                                date = f"2023-{month:02d}-01"
                                filename = f"{date}_{base}{suffix}.pdf"
                                sample_file = os.path.join(self.temp_dir, "banking/uk", "2023", filename)
                                with open(sample_file, 'w') as f:
                                    f.write(f"Sample UK bank document for {base}{suffix} on {date}")
            elif 'patterns' in bank:
                for pattern_info in bank['patterns']:
                    base = pattern_info['base']
                    date = "2023-12-31"
                    filename = f"{date}_{base}.pdf"
                    sample_file = os.path.join(self.temp_dir, "banking/uk", "2023", filename)
                    with open(sample_file, 'w') as f:
                        f.write(f"Sample UK bank document for {base} on {date}")
        
        # Additional documents
        for doc in self.dummy_config['additional']:
            if 'patterns' in doc:
                for pattern_info in doc['patterns']:
                    base = pattern_info['base']
                    date = "2023-12-31"
                    filename = f"{date}_{base}.pdf"
                    sample_file = os.path.join(self.temp_dir, "tax/us", "2023", filename)
                    with open(sample_file, 'w') as f:
                        f.write(f"Sample additional document for {base} on {date}")
        
        return self.temp_dir
    
    def test_base_config_structure(self):
        """Test that the base config has the expected structure."""
        # Verify the base categories as mentioned in the README
        assert 'employment' in self.base_config, "Employment section missing from base config"
        assert 'investment' in self.base_config, "Investment section missing from base config"
        assert 'bank' in self.base_config, "Bank section missing from base config"
        assert 'additional' in self.base_config, "Additional section missing from base config"
        
        # Check employment patterns
        assert 'patterns' in self.base_config['employment']
        assert 'payslip' in self.base_config['employment']['patterns']
        assert 'p45' in self.base_config['employment']['patterns']
        assert 'p60' in self.base_config['employment']['patterns']
        
        # Check investment patterns
        assert 'us' in self.base_config['investment']
        assert 'uk' in self.base_config['investment']
        assert 'patterns' in self.base_config['investment']['us']
        assert 'patterns' in self.base_config['investment']['uk']
        
        # Verify frequency values
        assert self.base_config['employment']['patterns']['payslip']['frequency'] == 'monthly'
        assert self.base_config['employment']['patterns']['p60']['frequency'] == 'yearly'
        assert self.base_config['employment']['patterns']['p45']['frequency'] == 'once'
    
    def test_dummy_config_structure(self):
        """Test that the dummy (private) config has the expected structure."""
        # Check sections mentioned in the README
        assert 'employment' in self.dummy_config, "Employment section missing from dummy config"
        assert 'investment' in self.dummy_config, "Investment section missing from dummy config"
        assert 'bank' in self.dummy_config, "Bank section missing from dummy config"
        assert 'additional' in self.dummy_config, "Additional section missing from dummy config"
        
        # Check employment is a list (flat structure)
        assert isinstance(self.dummy_config['employment'], list), "Employment should be a flat list"
        # Check each employer has required fields
        for employer in self.dummy_config['employment']:
            assert 'id' in employer, "Employer should have an id"
            # Name is optional if entity_id is provided
            if 'entity_id' not in employer:
                assert 'name' in employer, "Employer without entity_id should have a name"
        
        # Check investment subsections
        assert 'us' in self.dummy_config['investment']
        assert 'uk' in self.dummy_config['investment']
        
        # Check bank subsections
        assert 'us' in self.dummy_config['bank']
        assert 'uk' in self.dummy_config['bank']
    
    def test_directory_mapping_structure(self):
        """Test that the directory mapping has the expected structure."""
        # Check that directory_mapping is the top-level key
        assert 'directory_mapping' in self.directory_mapping
        mapping = self.directory_mapping['directory_mapping']
        
        # Check that all sections are present
        assert 'employment' in mapping
        assert 'investment_us' in mapping
        assert 'investment_uk' in mapping
        assert 'bank_uk' in mapping
        assert 'bank_us' in mapping
        assert 'additional' in mapping
        
        # Check that they are all lists
        assert isinstance(mapping['employment'], list)
        assert isinstance(mapping['investment_us'], list)
        assert isinstance(mapping['investment_uk'], list)
        assert isinstance(mapping['bank_uk'], list)
        assert isinstance(mapping['bank_us'], list)
        assert isinstance(mapping['additional'], list)
    
    def test_checker_initialization(self):
        """Test that the FinancialDocumentManager initializes correctly with the config files."""
        # Verify that the checker has loaded the configurations
        assert self.checker.base_config is not None
        assert self.checker.private_config is not None
        assert self.checker.directory_mapping is not None
        
        # Verify that required_patterns has been populated
        assert self.checker.required_patterns is not None
        assert 'employment' in self.checker.required_patterns
        assert 'investment_us' in self.checker.required_patterns
        assert 'investment_uk' in self.checker.required_patterns
        assert 'bank_uk' in self.checker.required_patterns
        assert 'bank_us' in self.checker.required_patterns
        assert 'additional' in self.checker.required_patterns
    
    def test_find_files_with_test_files(self):
        """Test finding files with test files."""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create the directory structure for test files
            os.makedirs(os.path.join(tmpdirname, "employment", "2023"), exist_ok=True)
            os.makedirs(os.path.join(tmpdirname, "banking", "uk", "2023"), exist_ok=True)
            os.makedirs(os.path.join(tmpdirname, "banking", "us", "2023"), exist_ok=True)
            os.makedirs(os.path.join(tmpdirname, "investments", "uk", "2023"), exist_ok=True)
            os.makedirs(os.path.join(tmpdirname, "investments", "us", "2023"), exist_ok=True)
            os.makedirs(os.path.join(tmpdirname, "tax", "us", "2023"), exist_ok=True)

            # Create test files
            # Employment
            for month in range(1, 13):
                date_str = f"2023-{month:02d}-01"
                for name in ["example-current-employer", "another-current-employer"]:
                    file_path = os.path.join(
                        tmpdirname, "employment", "2023", f"{date_str}_{name}.pdf"
                    )
                    with open(file_path, "w") as f:
                        f.write(f"Test file {file_path}")

            # Banking UK
            for month in range(1, 13):
                date_str = f"2023-{month:02d}-01"
                for account_type in ["joint", "savings"]:
                    file_path = os.path.join(
                        tmpdirname,
                        "banking", 
                        "uk", 
                        "2023", 
                        f"{date_str}_example-uk-bank_{account_type}.pdf"
                    )
                    with open(file_path, "w") as f:
                        f.write(f"Test file {file_path}")

            # End of year banking UK
            end_of_year_uk_banking = os.path.join(
                tmpdirname, "banking", "uk", "2023", "2023-12-31_another-uk-bank.pdf"
            )
            with open(end_of_year_uk_banking, "w") as f:
                f.write(f"Test file {end_of_year_uk_banking}")

            # End of year investments UK
            for name in ["example-uk-investment", "another-uk-investment"]:
                file_path = os.path.join(
                    tmpdirname, "investments", "uk", "2023", f"2023-12-31_{name}.pdf"
                )
                with open(file_path, "w") as f:
                    f.write(f"Test file {file_path}")

            # End of year investments US
            for name in ["example-us-investment", "another-us-investment"]:
                file_path = os.path.join(
                    tmpdirname, "investments", "us", "2023", f"2023-12-31_{name}.pdf"
                )
                with open(file_path, "w") as f:
                    f.write(f"Test file {file_path}")

            # End of year tax documents
            for name in [
                "example-tax-return",
                "EXAMPLE-E-FILE",
                "EXAMPLE_Federal",
                "EXAMPLE_FinCEN",
            ]:
                file_path = os.path.join(
                    tmpdirname, "tax", "us", "2023", f"2023-12-31_{name}.pdf"
                )
                with open(file_path, "w") as f:
                    f.write(f"Test file {file_path}")

            # Create test entities file
            test_entities = {
                "entities": [
                    {
                        "id": "example-employer",
                        "name": "Example Current Employer",
                        "type": "employer",
                        "url": "https://example-employer.com",
                        "contact": {"email": "hr@example-employer.com"}
                    },
                    {
                        "id": "another-employer",
                        "name": "Another Current Employer",
                        "type": "employer",
                        "url": "https://another-employer.com",
                        "contact": {"email": "hr@another-employer.com"}
                    },
                    {
                        "id": "example-investment",
                        "name": "Example Investment Platform",
                        "type": "investment",
                        "url": "https://example-investment.com",
                        "contact": {"email": "support@example-investment.com"}
                    },
                    {
                        "id": "another-investment",
                        "name": "Another Investment Platform",
                        "type": "investment",
                        "url": "https://another-investment.com",
                        "contact": {"email": "support@another-investment.com"}
                    },
                    {
                        "id": "example-bank",
                        "name": "Example Bank",
                        "type": "bank",
                        "url": "https://example-bank.com",
                        "contact": {"email": "support@example-bank.com"}
                    },
                    {
                        "id": "another-bank",
                        "name": "Another Bank",
                        "type": "bank",
                        "url": "https://another-bank.com",
                        "contact": {"email": "support@another-bank.com"}
                    }
                ]
            }
            
            entities_file = os.path.join(tmpdirname, "test_entities.yml")
            with open(entities_file, "w") as f:
                yaml.dump(test_entities, f)

            # Create test config file
            config_file = os.path.join(tmpdirname, "test_config.yml")
            config_content = {
                "employment": {
                    "patterns": {
                        "payslip": {"frequency": "monthly"},
                        "p60": {"frequency": "yearly"},
                        "p45": {"frequency": "once"}
                    },
                    "current": [
                        {
                            "id": "example-employer",
                            "name": "EXAMPLE_CURRENT_EMPLOYER",
                            "frequency": "monthly",
                            "patterns": ["example-current-employer"],
                            "start_date": "2020-01-01"
                        },
                        {
                            "id": "another-employer",
                            "name": "ANOTHER_CURRENT_EMPLOYER",
                            "frequency": "monthly",
                            "patterns": ["another-current-employer"],
                            "start_date": "2021-01-01"
                        }
                    ]
                },
                "investment": {
                    "uk": [
                        {"id": "example-uk-investment", "name": "EXAMPLE_UK_INVESTMENT", "patterns": ["example-uk-investment"]},
                        {"id": "another-uk-investment", "name": "ANOTHER_UK_INVESTMENT", "patterns": ["another-uk-investment"]}
                    ],
                    "us": [
                        {"id": "example-us-investment", "name": "EXAMPLE_US_INVESTMENT", "patterns": ["example-us-investment"]},
                        {"id": "another-us-investment", "name": "ANOTHER_US_INVESTMENT", "patterns": ["another-us-investment"]}
                    ]
                },
                "bank": {
                    "uk": [
                        {
                            "id": "example-uk-bank",
                            "name": "EXAMPLE_UK_BANK",
                            "account_types": [
                                {
                                    "id": "example-uk-bank-joint",
                                    "name": "Joint Account",
                                    "patterns": [{"base": "example-uk-bank", "account_type": "joint"}]
                                },
                                {
                                    "id": "example-uk-bank-savings",
                                    "name": "Savings",
                                    "patterns": [{"base": "example-uk-bank", "account_type": "savings"}]
                                }
                            ]
                        },
                        {
                            "id": "another-uk-bank",
                            "name": "ANOTHER_UK_BANK",
                            "patterns": ["another-uk-bank"]
                        }
                    ],
                    "us": []
                },
                "additional": [
                    {"id": "example-tax-return", "name": "EXAMPLE_TAX_RETURN", "patterns": ["example-tax-return"]},
                    {"id": "example-e-file", "name": "EXAMPLE_E_FILE", "patterns": ["EXAMPLE-E-FILE"]},
                    {"id": "example-federal", "name": "EXAMPLE_FEDERAL_TAX", "patterns": ["EXAMPLE_Federal"]},
                    {"id": "example-fincen", "name": "EXAMPLE_FINCEN", "patterns": ["EXAMPLE_FinCEN"]}
                ]
            }
            with open(config_file, "w") as f:
                yaml.dump(config_content, f)

            # Create directory mapping file
            directory_mapping = {
                "directory_mapping": {
                    "employment": ["employment"],
                    "bank_uk": ["banking/uk"],
                    "bank_us": ["banking/us"],
                    "investment_uk": ["investments/uk"],
                    "investment_us": ["investments/us"],
                    "additional": ["tax/us"]
                }
            }
            
            directory_mapping_file = os.path.join(tmpdirname, "test_directory_mapping.yml")
            with open(directory_mapping_file, "w") as f:
                yaml.dump(directory_mapping, f)

            # Use the FinancialDocumentManager to find the files
            checker = FinancialDocumentManager(
                config_file=config_file,
                base_path=tmpdirname,
                entities_file=entities_file,
                directory_mapping_file=directory_mapping_file
            )
            
            # Print debug information
            print(f"Base directory: {tmpdirname}")
            print(f"Directory mapping: {directory_mapping}")
            print(f"Test files in employment directory: {os.listdir(os.path.join(tmpdirname, 'employment', '2023'))}")
            
            available_years = checker.list_available_years()
            assert "2023" in available_years, "2023 should be found as an available year"
            
            # Test finding files for employment patterns
            for pattern_info in checker.required_patterns['employment']:
                pattern = pattern_info['pattern']
                matches = checker.find_files_matching_pattern(pattern, year='2023', category='employment')
                # We should find some files for at least some patterns
                if "example-current-employer" in pattern or "another-current-employer" in pattern:
                    assert len(matches) > 0, f"Should find files for pattern: {pattern}"
    
    def test_check_year_with_test_files(self):
        """Test the check_year functionality with test files."""
        # Create test files
        temp_dir = self.create_test_files()
        
        # Create a new checker with the temp directory as base path
        test_checker = FinancialDocumentManager(
            base_path=temp_dir, 
            config_file=self.base_config_file,
            private_config_file=self.dummy_config_file,
            directory_mapping_file=self.directory_mapping_file
        )
        
        # Check the year 2023
        results = test_checker.check_year('2023', list_missing=True)
        
        # We should get a valid result dictionary
        assert 'year' in results
        assert results['year'] == '2023'
        assert 'missing_files' in results
        assert 'found_files' in results
        assert 'all_found' in results
    
    def test_config_compatibility(self):
        """Test that the base config and private config are compatible."""
        # The categories in private config should match those in base config
        for category in ['employment', 'investment', 'bank', 'additional']:
            assert category in self.base_config
            assert category in self.dummy_config
        
        # The subcategories should also match
        assert 'us' in self.base_config['investment']
        assert 'uk' in self.base_config['investment']
        assert 'us' in self.dummy_config['investment']
        assert 'uk' in self.dummy_config['investment']
        
        assert 'uk' in self.base_config['bank']
        assert 'us' in self.base_config['bank']
        assert 'uk' in self.dummy_config['bank']
        assert 'us' in self.dummy_config['bank']
    
    def test_frequency_values(self):
        """Test that frequency values are as expected."""
        # From base config
        base_frequencies = {}
        for pattern_name, pattern_info in self.base_config['employment']['patterns'].items():
            base_frequencies[pattern_name] = pattern_info['frequency']
        
        assert base_frequencies['payslip'] == 'monthly'
        assert base_frequencies['p60'] == 'yearly'
        assert base_frequencies['p45'] == 'once'
        
        # From private config (using flat structure)
        for employer in self.dummy_config['employment']:
            assert 'frequency' in employer
            assert employer['frequency'] in ['monthly', 'quarterly', 'yearly', 'once', 'annual']
    
    def test_urls_in_private_config(self):
        """Test that URLs are now in entities instead of directly in private config."""
        # Create a entities file to test with
        entities_file = os.path.join(self.temp_dir, "test_entities.yml")
        test_entities = {
            "entities": [
                {
                    "id": "example-employer",
                    "name": "Example Current Employer",
                    "type": "employer",
                    "url": "https://employer.example.com",
                    "contact": {"email": "contact@employer.com"}
                },
                {
                    "id": "example-investment",
                    "name": "Example Investment Platform",
                    "type": "investment",
                    "url": "https://investment.example.com",
                    "contact": {"email": "contact@investment.com"}
                },
                {
                    "id": "example-bank",
                    "name": "Example Bank",
                    "type": "bank",
                    "url": "https://bank.example.com",
                    "contact": {"email": "contact@bank.com"}
                }
            ]
        }
        with open(entities_file, 'w') as f:
            yaml.dump(test_entities, f)
        
        # Create a checker with the entities file
        from finx.entities import EntityManager
        
        # Initialize entity manager with the test file
        entity_manager = EntityManager(entities_file)
        entities = entity_manager.load_entities()
        
        # Verify entities have URLs
        url_count = 0
        for entity in entities:
            if entity.url:
                url_count += 1
        
        assert url_count >= 3, "Not enough URLs found in the entities"
        
        # Verify that the correct entity has the expected URL
        for entity in entities:
            if entity.name == "Example Current Employer":
                assert entity.url == "https://employer.example.com"
            elif entity.name == "Example Investment Platform":
                assert entity.url == "https://investment.example.com"
            elif entity.name == "Example Bank":
                assert entity.url == "https://bank.example.com"
    
    def test_start_end_dates(self):
        """Test that start and end dates follow the expected format."""
        # Sample a few items to check date format
        for employer in self.dummy_config['employment']:
            if 'start_date' in employer:
                start_date = employer['start_date']
                # Should be a string in YYYY-MM-DD format
                assert isinstance(start_date, str)
                assert len(start_date) == 10
                assert start_date[4] == '-' and start_date[7] == '-'
            
            # End date can be null for current relationships
            if 'end_date' in employer and employer['end_date'] is not None:
                end_date = employer['end_date']
                assert isinstance(end_date, str)
                assert len(end_date) == 10
                assert end_date[4] == '-' and end_date[7] == '-'
    
    def test_cli_commands_with_config_files(self):
        """Test that the CLI commands described in README work with our config files."""
        # Import the main function from cli_typer
        from finx.cli_typer import main
        
        # Create test files
        temp_dir = self.create_test_files()
        
        # Patch logging and sys.argv to avoid actual console output
        import io
        import sys
        from unittest.mock import patch
        
        # Test tax status command
        with patch('sys.argv', [
            'finx', 'tax', 'status',
            '--year', '2023',
            '--base-path', temp_dir,
            '--config-file', str(self.base_config_file),
            '--private-config-file', str(self.dummy_config_file),
            '--directory-mapping-file', str(self.directory_mapping_file)
        ]):
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('logging.Logger.info'):
                    with patch('logging.Logger.warning') as mock_warning:
                        # Run the command and catch SystemExit since Typer will exit
                        try:
                            main()
                        except SystemExit as e:
                            # Check exit code (0 for success)
                            assert e.code == 0 or e.code == 1, "Expected exit code 0 or 1"
                        
                        # Check for warning messages which we can see in the output
                        assert len(mock_warning.call_args_list) > 0, "Expected warning messages in log output"
        
        # Test tax missing command
        with patch('sys.argv', [
            'finx', 'tax', 'missing',
            '--year', '2023',
            '--base-path', temp_dir,
            '--config-file', str(self.base_config_file),
            '--private-config-file', str(self.dummy_config_file),
            '--directory-mapping-file', str(self.directory_mapping_file),
            '--format', 'text'
        ]):
            with patch('sys.stdout', new_callable=io.StringIO):
                with patch('logging.Logger.info'):
                    with patch('logging.Logger.warning') as mock_warning:
                        # Run the command and catch SystemExit
                        try:
                            main()
                        except SystemExit as e:
                            # Check exit code (0 for success)
                            assert e.code == 0 or e.code == 1, "Expected exit code 0 or 1"
                        
                        # Check for warning messages
                        assert len(mock_warning.call_args_list) > 0, "Expected warning messages in log output"
    
    def test_dual_id_system(self):
        """Test that the dual ID system is implemented correctly."""
        # Check ids in dummy config
        for employer in self.dummy_config['employment']:
            if isinstance(employer, dict):
                assert 'id' in employer, "Each employer should have an id"
                # entity_id might not be in all entries during transition
                if 'entity_id' in employer:
                    assert employer['entity_id'], "entity_id should not be empty if present"
                
        # Check ids in investment section
        for region in ['uk', 'us']:
            for investment in self.dummy_config['investment'][region]:
                if isinstance(investment, dict):
                    assert 'id' in investment, f"Each investment in {region} should have an id"
                    # entity_id might not be in all entries during transition
                    if 'entity_id' in investment:
                        assert investment['entity_id'], "entity_id should not be empty if present"
        
        # Check ids in bank section
        for region in ['uk', 'us']:
            for bank in self.dummy_config['bank'][region]:
                if isinstance(bank, dict):
                    assert 'id' in bank, f"Each bank in {region} should have an id"
                    # entity_id might not be in all entries during transition
                    if 'entity_id' in bank:
                        assert bank['entity_id'], "entity_id should not be empty if present"
                    
                    # Check account types if present
                    if 'account_types' in bank:
                        for account in bank['account_types']:
                            assert 'id' in account, "Each account type should have an id"
                            # entity_id might not be in all entries during transition
                            if 'entity_id' in account:
                                assert account['entity_id'], "entity_id should not be empty if present"
        
        # Check ids in additional section
        for doc in self.dummy_config['additional']:
            if isinstance(doc, dict):
                assert 'id' in doc, "Each additional document should have an id"
                # entity_id might not be in all entries during transition
                if 'entity_id' in doc:
                    assert doc['entity_id'], "entity_id should not be empty if present"
    
    def test_entity_id_references(self):
        """Test that entity_id references exist in the entities file."""
        # Create test entities file
        entities_file = os.path.join(self.temp_dir, "test_entities.yml")
        test_entities = {
            "entities": [
                {
                    "id": "test-employer",
                    "name": "Test Employer",
                    "type": "employer"
                },
                {
                    "id": "test-bank",
                    "name": "Test Bank",
                    "type": "bank"
                },
                {
                    "id": "test-investment",
                    "name": "Test Investment",
                    "type": "investment"
                }
            ]
        }
        
        with open(entities_file, 'w') as f:
            yaml.dump(test_entities, f)
        
        # Create test config with entity_id references
        config_file = os.path.join(self.temp_dir, "test_config.yml")
        test_config = {
            "employment": [
                {
                    "id": "test-employer-payslip",
                    "entity_id": "test-employer",
                    "name": "Test Employer",
                    "frequency": "monthly",
                    "patterns": ["test-employer"]
                }
            ],
            "bank": {
                "uk": [
                    {
                        "id": "test-bank-statement",
                        "entity_id": "test-bank",
                        "name": "Test Bank",
                        "patterns": ["test-bank-statement"]
                    }
                ]
            },
            "investment": {
                "uk": [
                    {
                        "id": "test-investment-statement",
                        "entity_id": "test-investment",
                        "name": "Test Investment",
                        "patterns": ["test-investment-statement"]
                    }
                ]
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Create a checker with the test files
        from finx.entities import EntityManager
        
        # Initialize entity manager with the test file
        entity_manager = EntityManager(entities_file)
        entities = entity_manager.load_entities()
        
        # Load the config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check that all entity_id references exist in entities
        entity_ids = {entity.id for entity in entities}
        
        # Check employment
        for employer in config['employment']:
            if 'entity_id' in employer:
                assert employer['entity_id'] in entity_ids, f"Entity ID {employer['entity_id']} not found in entities"
        
        # Check bank
        for region in ['uk']:
            for bank in config['bank'][region]:
                if 'entity_id' in bank:
                    assert bank['entity_id'] in entity_ids, f"Entity ID {bank['entity_id']} not found in entities"
        
        # Check investment
        for region in ['uk']:
            for investment in config['investment'][region]:
                if 'entity_id' in investment:
                    assert investment['entity_id'] in entity_ids, f"Entity ID {investment['entity_id']} not found in entities" 