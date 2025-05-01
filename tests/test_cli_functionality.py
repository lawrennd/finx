import os
import sys
import json
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import yaml
from finx.entities import Entity, EntityType

# This file tests CLI functionality regardless of implementation
# It should work with both argparse and Typer

class TestCLIFunctionality:
    """Test CLI functionality independent of implementation."""
    
    @pytest.fixture
    def mock_checker(self):
        """Return a mock FinancialDocumentManager instance."""
        with patch('finx.cli_typer.FinancialDocumentManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def setup_test_files(self):
        """Create test files and configs for integration testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create directory structure
            os.makedirs(os.path.join(tmpdirname, "employment", "2023"), exist_ok=True)
            os.makedirs(os.path.join(tmpdirname, "banking", "uk", "2023"), exist_ok=True)
            
            # Create sample files
            test_file_path = os.path.join(tmpdirname, "employment", "2023", "2023-01-01_test-employer.pdf")
            with open(test_file_path, "w") as f:
                f.write("Test file content")
            
            # Create test configs
            base_config = {
                "employment": {
                    "patterns": {
                        "payslip": {"frequency": "monthly"},
                        "p60": {"frequency": "yearly"}
                    }
                },
                "investment": {
                    "uk": ["test_investment"],
                    "us": ["test_investment_us"]
                },
                "bank": {
                    "uk": ["test_bank_uk"],
                    "us": ["test_bank_us"]
                }
            }
            
            private_config = {
                "employment": {
                    "current": [
                        {
                            "name": "TEST_EMPLOYER",
                            "patterns": ["test-employer"],
                            "frequency": "monthly",
                            "start_date": "2022-01-01"
                        }
                    ]
                }
            }
            
            mapping_config = {
                "directory_mapping": {
                    "employment": ["employment"],
                    "bank_uk": ["banking/uk"]
                }
            }
            
            entities_config = {
                "entities": [
                    {
                        "name": "TEST_EMPLOYER",
                        "type": "employer",
                        "contact": {"email": "test@example.com"},
                        "url": "https://test-employer.com"
                    }
                ]
            }
            
            base_config_path = os.path.join(tmpdirname, "finx_base.yml")
            private_config_path = os.path.join(tmpdirname, "finx_private.yml")
            mapping_config_path = os.path.join(tmpdirname, "directory_mapping.yml")
            entities_config_path = os.path.join(tmpdirname, "entities.yml")
            
            with open(base_config_path, "w") as f:
                yaml.dump(base_config, f)
                
            with open(private_config_path, "w") as f:
                yaml.dump(private_config, f)
                
            with open(mapping_config_path, "w") as f:
                yaml.dump(mapping_config, f)
                
            with open(entities_config_path, "w") as f:
                yaml.dump(entities_config, f)
                
            yield {
                "dir": tmpdirname,
                "base_config": base_config_path,
                "private_config": private_config_path,
                "mapping_config": mapping_config_path,
                "entities_config": entities_config_path,
                "test_file": test_file_path
            }
    
    def test_tax_status_functionality(self, mock_checker):
        """Test that the tax status command correctly checks document status."""
        from finx.cli_typer import main
        
        # Setup mock behavior
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.check_year.return_value = {
            'year': '2023',
            'all_found': True,
            'found_files': ['/path/to/file.pdf'],
            'missing_files': []
        }
        
        with patch('sys.argv', ['finx', 'tax', 'status']):
            with patch('sys.stdout'):  # Suppress stdout
                with pytest.raises(SystemExit) as e:
                    main()
                # Success exit code
                assert e.value.code == 0
        
        # Verify expected behavior
        mock_checker.list_available_years.assert_called_once()
        mock_checker.check_year.assert_called_once()
    
    def test_tax_status_with_year_functionality(self, mock_checker):
        """Test that the tax status command with year checks specific year."""
        from finx.cli_typer import main
        
        # Setup mock behavior
        mock_checker.check_year.return_value = {
            'year': '2022',
            'all_found': True,
            'found_files': ['/path/to/file.pdf'],
            'missing_files': []
        }
        
        with patch('sys.argv', ['finx', 'tax', 'status', '--year', '2022']):
            with patch('sys.stdout'):  # Suppress stdout
                with pytest.raises(SystemExit) as e:
                    main()
                # Success exit code
                assert e.value.code == 0
        
        # Verify expected behavior
        mock_checker.check_year.assert_called_once_with('2022', list_missing=False)
    
    def test_tax_missing_functionality(self, mock_checker):
        """Test that the tax missing command lists missing documents."""
        from finx.cli_typer import main
        
        # Setup mock behavior
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.check_year.return_value = {
            'year': '2023',
            'all_found': False,
            'found_files': [],
            'missing_files': [
                {
                    'path': '/path/to/missing.pdf',
                    'name': 'test_doc',
                    'frequency': 'yearly',
                    'url': 'https://example.com'
                }
            ]
        }
        
        with patch('sys.argv', ['finx', 'tax', 'missing']):
            with patch('sys.stdout'):  # Suppress stdout
                with pytest.raises(SystemExit) as e:
                    main()
                # Success exit code
                assert e.value.code == 0
        
        # Verify expected behavior
        mock_checker.list_available_years.assert_called_once()
        mock_checker.check_year.assert_called_once_with('2023', list_missing=True)
    
    def test_tax_missing_with_json_functionality(self, mock_checker):
        """Test that the tax missing command with JSON format outputs JSON."""
        from finx.cli_typer import main
        
        # Setup mock behavior
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.check_year.return_value = {
            'year': '2023',
            'all_found': False,
            'found_files': [],
            'missing_files': [
                {
                    'path': '/path/to/missing.pdf',
                    'name': 'test_doc',
                    'frequency': 'yearly',
                    'url': 'https://example.com'
                }
            ]
        }
        
        with patch('sys.argv', ['finx', 'tax', 'missing', '--format', 'json']):
            with patch('json.dumps') as mock_json_dumps:
                with patch('sys.stdout'):  # Suppress stdout
                    with pytest.raises(SystemExit) as e:
                        main()
                    # Success exit code
                    assert e.value.code == 0
        
        # Verify expected behavior
        mock_json_dumps.assert_called_once()
        # Just check that json.dumps was called, not the exact format
        # since this might change between argparse and Typer implementations
    
    def test_tax_update_dates_functionality(self, mock_checker):
        """Test that the tax update-dates command updates YAML with dates."""
        from finx.cli_typer import main
        
        with patch('sys.argv', ['finx', 'tax', 'update-dates']):
            with patch('sys.stdout'):  # Suppress stdout
                with pytest.raises(SystemExit) as e:
                    main()
                # Success exit code
                assert e.value.code == 0
        
        # Verify expected behavior
        mock_checker.update_yaml_with_dates.assert_called_once()
    
    def test_entities_check_functionality(self):
        """Test that the entities check command identifies missing entities."""
        # This needs to be tested differently since it uses Click directly
        # We'll test the underlying function instead
        from finx.cli_typer import extract_entity_names
        
        # Test config parsing with how the function is currently implemented
        test_config = {
            'employment': {
                'current': [
                    {'name': 'ENTITY1', 'patterns': ['pattern1']},
                    {'name': 'ENTITY2', 'patterns': ['pattern2']}
                ]
            },
            'investment': {
                'uk': [
                    {'name': 'INVESTMENT1'},
                    'INVESTMENT2'
                ]
            },
            'bank': {
                'us': [
                    {'name': 'BANK1'},
                    'BANK2'
                ]
            }
        }
        
        result = extract_entity_names(test_config)
        assert len(result) == 6
        assert 'ENTITY1' in result
        assert 'ENTITY2' in result
        assert 'INVESTMENT1' in result
        assert 'INVESTMENT2' in result
        assert 'BANK1' in result
        assert 'BANK2' in result
    
    def test_entities_list_with_format_functionality(self):
        """Test that the entities list command supports different output formats."""
        from finx.cli_typer import main
        
        # Test data - create Entity objects instead of dictionaries
        test_entity = Entity(
            name='Test Entity',
            type=EntityType.BANK,
            contact={'email': 'test@example.com', 'primary': 'John Doe'},
            url='https://example.com'
        )
        test_entities = [test_entity]
        
        # Test for JSON format
        with patch('finx.cli_typer.EntityManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_entities.return_value = test_entities
            
            with patch('sys.argv', ['finx', 'entities', 'list', '--format', 'json']):
                with patch('json.dumps') as mock_json_dumps:
                    with patch('typer.echo'):
                        with pytest.raises(SystemExit) as e:
                            main()
                        # Success exit code
                        assert e.value.code == 0
            
            # Verify expected behavior
            mock_manager.list_entities.assert_called_once()
            # Verify that to_dict was called on the entity to convert it to JSON-serializable format
            mock_json_dumps.assert_called_once()
            # Extract the first argument of the first positional argument
            # It should be a list of dictionaries converted from Entity objects
            first_arg = mock_json_dumps.call_args[0][0]
            assert isinstance(first_arg, list)
            assert len(first_arg) == 1
            # Entity is converted to dict before JSON serialization
            assert isinstance(first_arg[0], dict)
            assert 'name' in first_arg[0]
            assert first_arg[0]['name'] == 'Test Entity'
        
        # Test for CSV format
        with patch('finx.cli_typer.EntityManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_entities.return_value = test_entities
            
            with patch('sys.argv', ['finx', 'entities', 'list', '--format', 'csv']):
                with patch('csv.DictWriter') as mock_csv_writer:
                    with patch('typer.echo'):
                        with pytest.raises(SystemExit) as e:
                            main()
                        # Success exit code
                        assert e.value.code == 0
            
            # Verify expected behavior
            mock_manager.list_entities.assert_called_once()
            # Can't easily verify the CSV output but we can check it was called
    
    def test_entities_check_with_format_functionality(self):
        """Test that the entities check command supports different output formats."""
        from finx.cli_typer import main
        
        # Test for JSON format
        with patch('finx.cli_typer.EntityManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.check_missing_entities.return_value = ['MISSING_ENTITY1', 'MISSING_ENTITY2']
            
            with patch('finx.cli_typer.extract_entity_names', return_value=['ENTITY1', 'MISSING_ENTITY1', 'MISSING_ENTITY2']):
                with patch('sys.argv', ['finx', 'entities', 'check', '--format', 'json']):
                    with patch('json.dumps') as mock_json_dumps:
                        with patch('typer.echo'):
                            with pytest.raises(SystemExit) as e:
                                main()
                            # Success exit code
                            assert e.value.code == 0
            
            # Verify expected behavior for JSON output
            mock_manager.check_missing_entities.assert_called_once()
            mock_json_dumps.assert_called_once()
            # We can't easily verify the exact output but we can check it was called with a dict
            assert isinstance(mock_json_dumps.call_args[0][0], dict)
            assert 'missing_entities' in mock_json_dumps.call_args[0][0]
        
        # Test for CSV format
        with patch('finx.cli_typer.EntityManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.check_missing_entities.return_value = ['MISSING_ENTITY1', 'MISSING_ENTITY2']
            
            with patch('finx.cli_typer.extract_entity_names', return_value=['ENTITY1', 'MISSING_ENTITY1', 'MISSING_ENTITY2']):
                with patch('sys.argv', ['finx', 'entities', 'check', '--format', 'csv']):
                    with patch('csv.writer') as mock_csv_writer:
                        with patch('typer.echo'):
                            with pytest.raises(SystemExit) as e:
                                main()
                            # Success exit code
                            assert e.value.code == 0
            
            # Verify expected behavior for CSV output
            mock_manager.check_missing_entities.assert_called_once()
            # Can't easily verify the CSV output but we can check it was called
    
    @pytest.mark.integration
    def test_cli_integration(self, setup_test_files):
        """Test CLI integration with real files and system calls."""
        # This test actually executes the CLI as a subprocess
        # Skip this test if not running integration tests
    
        files = setup_test_files
        test_dir = files["dir"]
    
        # Call the CLI with the test files
        # Use correct parameter names based on CLI help output
        cmd = [
            sys.executable, "-m", "finx.cli",
            "tax", "status",
            "--base-path", test_dir,
            "--config-file", files["base_config"],
            "--private-config-file", files["private_config"],
            "--directory-mapping-file", files["mapping_config"],
            "--entities-file", files["entities_config"]
        ]
    
        # Print debug info about the test files
        print(f"Test directory: {test_dir}")
        print(f"Base config: {files['base_config']}")
        print(f"Private config: {files['private_config']}")
        print(f"Mapping config: {files['mapping_config']}")
        print(f"Entities config: {files['entities_config']}")
    
        # Run the CLI command and capture output
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # Timeout after 10 seconds
            )
    
            # Print result information for debugging
            print(f"Return code: {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
    
            # Don't verify the return code - either 0 or 1 is acceptable
            # The tax_status_command returns 1 if any documents are missing,
            # which is expected in our test setup
            
            # Verify output contains expected text
            assert "Checking documents for year" in result.stdout
    
        except subprocess.TimeoutExpired:
            pytest.fail("CLI command timed out")
        except Exception as e:
            pytest.fail(f"CLI integration test failed: {str(e)}\nstdout: {result.stdout}\nstderr: {result.stderr}")
    
    def test_error_handling_functionality(self, mock_checker):
        """Test CLI error handling works correctly."""
        from finx.cli_typer import main
        
        # Make the mock throw an exception
        mock_checker.list_available_years.side_effect = Exception("Test error")
        
        with patch('sys.argv', ['finx', 'tax', 'status']):
            with patch('sys.stderr'):  # Suppress stderr
                # In the error case, main() returns 1 instead of raising SystemExit
                result = main()
                assert result == 1 