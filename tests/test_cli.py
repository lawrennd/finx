import pytest
from unittest.mock import patch, MagicMock
from unittest import TestCase
from tax_assistant.cli import main, tax_status_command, tax_missing_command, tax_update_dates_command, invest_command
import sys
import logging
from pathlib import Path
import argparse

class TestCLI(TestCase):
    def setUp(self):
        """Set up common test fixtures."""
        # Mock Path.stat() to return fake file stats
        self.stat_mock = MagicMock()
        self.stat_mock.st_size = 1024 * 1024  # 1MB
        self.stat_mock.st_mtime = 1678900000  # Some timestamp
        self.path_stat_patcher = patch('pathlib.Path.stat', return_value=self.stat_mock)
        self.path_stat_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.path_stat_patcher.stop()

    def test_cli_tax_status_default(self):
        """Test CLI tax status command with default arguments."""
        with patch('sys.argv', ['finx', 'tax', 'status']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = {
                    'all_found': True
                }
                
                assert main(None) == 0
                mock_instance.check_year.assert_called_once()

    def test_cli_tax_status_with_year(self):
        """Test CLI tax status command with specific year."""
        with patch('sys.argv', ['finx', 'tax', 'status', '--year', '2023']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.check_year.return_value = {
                    'all_found': True
                }
                
                assert main(None) == 0
                mock_instance.check_year.assert_called_once_with('2023', list_missing=False)

    def test_cli_tax_update_dates(self):
        """Test CLI tax update-dates command."""
        with patch('sys.argv', ['finx', 'tax', 'update-dates']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                
                with self.assertLogs(level='INFO') as log_capture:
                    assert main(None) == 0
                    
                    # Verify log messages
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Updating YAML with inferred dates" in msg for msg in log_messages)
                    assert any("YAML updated successfully!" in msg for msg in log_messages)
                    
                mock_instance.update_yaml_with_dates.assert_called_once()

    def test_cli_tax_status_with_base_path(self):
        """Test CLI with base path without verbose flag."""
        with patch('sys.argv', ['finx', 'tax', 'status', '--base-path', '/test/path']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = {
                    'all_found': True
                }
                
                assert main(None) == 0
                # Check that TaxDocumentChecker was created with correct args
                mock_checker.assert_called_once()
                # Verify that base_path was passed correctly
                args, kwargs = mock_checker.call_args
                assert kwargs['base_path'] == '/test/path'
                assert kwargs['verbose'] == False

    def test_cli_tax_status_with_base_path_verbose(self):
        """Test CLI with base path and verbose flag."""
        with patch('sys.argv', ['finx', 'tax', 'status', '--base-path', '/test/path', '--verbose']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = {
                    'all_found': True
                }
                
                assert main(None) == 0
                # Check that TaxDocumentChecker was created with correct args
                mock_checker.assert_called_once()
                # Verify that base_path and verbose were passed correctly
                args, kwargs = mock_checker.call_args
                assert kwargs['base_path'] == '/test/path'
                assert kwargs['verbose'] == True

    def test_cli_tax_missing(self):
        """Test CLI tax missing command."""
        with patch('sys.argv', ['finx', 'tax', 'missing']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = {
                    'year': '2023',
                    'missing_files': [
                        {
                            'path': '/test/missing.pdf',
                            'name': 'test_doc',
                            'frequency': 'yearly',
                            'url': 'https://example.com'
                        }
                    ],
                    'found_files': [],
                    'errors': [],
                    'all_found': False
                }
                
                with patch('sys.stdout'):
                    assert main(None) == 0
                mock_instance.check_year.assert_called_once_with('2023', list_missing=True)

    def test_cli_tax_status_with_no_years_found(self):
        """Test CLI when no tax years are found in the directory."""
        with patch('sys.argv', ['finx', 'tax', 'status', '--base-path', '/empty/path']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = []
                
                with patch('logging.Logger.warning') as mock_warning:
                    assert main(None) == 0
                    # Verify warning was logged
                    mock_warning.assert_called_with("No tax years found in the directory.")

    def test_cli_tax_missing_with_json_format(self):
        """Test CLI with JSON output format."""
        with patch('sys.argv', ['finx', 'tax', 'missing', '--format', 'json']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = {
                    'year': '2023',
                    'missing_files': [
                        {
                            'path': '/test/missing.pdf',
                            'name': 'test_doc',
                            'frequency': 'yearly',
                            'url': 'https://example.com'
                        }
                    ],
                    'found_files': [],
                    'errors': [],
                    'all_found': False
                }
                
                with patch('json.dumps') as mock_json_dumps:
                    assert main(None) == 0
                    # Verify that JSON formatting was used
                    mock_json_dumps.assert_called_once()
                    # Verify the data structure passed to json.dumps
                    args, kwargs = mock_json_dumps.call_args
                    assert 'missing_files' in args[0]
                    assert isinstance(args[0]['missing_files'], list)
                    assert len(args[0]['missing_files']) == 1
                    assert args[0]['missing_files'][0]['url'] == 'https://example.com'

    def test_cli_tax_missing_with_csv_format(self):
        """Test CLI with CSV output format."""
        with patch('sys.argv', ['finx', 'tax', 'missing', '--format', 'csv']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = {
                    'year': '2023',
                    'missing_files': [
                        {
                            'path': '/test/missing.pdf',
                            'name': 'test_doc',
                            'frequency': 'yearly',
                            'url': 'https://example.com'
                        }
                    ],
                    'found_files': [],
                    'errors': [],
                    'all_found': False
                }
                
                with patch('csv.DictWriter') as mock_csv_writer:
                    mock_instance = MagicMock()
                    mock_csv_writer.return_value = mock_instance
                    
                    assert main(None) == 0
                    # Verify that CSV formatting was used
                    mock_csv_writer.assert_called_once()
                    # Verify the field names passed to DictWriter
                    args, kwargs = mock_csv_writer.call_args
                    assert 'fieldnames' in kwargs
                    assert 'url' in kwargs['fieldnames']
                    assert 'frequency' in kwargs['fieldnames']

    def test_cli_tax_zip(self):
        """Test CLI tax zip command."""
        with patch('sys.argv', ['finx', 'tax', 'zip', '--year', '2023']):
            with patch('tax_assistant.cli.create_zip_archive') as mock_zip_creator:
                mock_zip_creator.return_value = True
                
                assert main(None) == 0
                # Verify that zip creator was called with correct year
                args, kwargs = mock_zip_creator.call_args
                assert kwargs['year'] == '2023'
                assert kwargs['dummy'] == False

    def test_cli_tax_zip_dummy(self):
        """Test CLI tax zip command in dummy mode."""
        with patch('sys.argv', ['finx', 'tax', 'zip', '--year', '2023', '--dummy']):
            with patch('tax_assistant.cli.create_zip_archive') as mock_zip_creator:
                mock_zip_creator.return_value = True
                
                assert main(None) == 0
                # Verify that zip creator was called with dummy mode
                args, kwargs = mock_zip_creator.call_args
                assert kwargs['year'] == '2023'
                assert kwargs['dummy'] == True

    def test_cli_with_no_command(self):
        """Test CLI with no command specified."""
        with patch('sys.argv', ['finx']):
            # Mock the parse_args function to return a namespace with required attributes
            with patch('tax_assistant.cli.parse_args') as mock_parse_args:
                mock_namespace = argparse.Namespace()
                mock_namespace.command = None
                mock_namespace.verbose = False
                mock_parse_args.return_value = mock_namespace
                
                with patch('builtins.print') as mock_print:
                    assert main(None) == 1
                    mock_print.assert_called_with("No command specified. Use --help to see available commands.")

    def test_cli_with_no_tax_subcommand(self):
        """Test CLI with tax command but no subcommand."""
        with patch('sys.argv', ['finx', 'tax']):
            # Mock the parse_args function to return a namespace with required attributes
            with patch('tax_assistant.cli.parse_args') as mock_parse_args:
                mock_namespace = argparse.Namespace()
                mock_namespace.command = 'tax'
                mock_namespace.verbose = False
                # Do not set 'func' attribute to simulate no subcommand
                mock_parse_args.return_value = mock_namespace
                
                with patch('builtins.print') as mock_print:
                    assert main(None) == 1
                    mock_print.assert_called_with("No tax subcommand specified. Use 'finx tax --help' to see available subcommands.")

    def test_cli_invest_placeholder(self):
        """Test CLI invest command (placeholder)."""
        with patch('sys.argv', ['finx', 'invest']):
            # Mock the parse_args function to return a namespace with required attributes
            with patch('tax_assistant.cli.parse_args') as mock_parse_args:
                mock_namespace = argparse.Namespace()
                mock_namespace.command = 'invest'
                mock_namespace.verbose = False
                mock_namespace.func = invest_command  # Set the function attribute
                mock_parse_args.return_value = mock_namespace
                
                with patch('builtins.print') as mock_print:
                    assert main(None) == 1
                    mock_print.assert_called_with("Investment tracking functionality is not yet implemented") 
