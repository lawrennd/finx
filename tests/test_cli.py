import pytest
from unittest.mock import patch, MagicMock
from unittest import TestCase
from tax_assistant.cli import main
import sys
import logging
from pathlib import Path

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

    def test_cli_default_behavior(self):
        """Test CLI default behavior (listing files)."""
        with patch('sys.argv', ['tax-document-lister']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.required_patterns = {
                    'banking': [{'pattern': '.*', 'name': 'test'}]
                }
                mock_instance.find_files_matching_pattern.return_value = ['/test/file.pdf']
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()

    def test_cli_with_year(self):
        """Test CLI with specific year argument."""
        with patch('sys.argv', ['tax-document-lister', '--year', '2023']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.required_patterns = {
                    'banking': [{'pattern': '.*', 'name': 'test'}]
                }
                mock_instance.find_files_matching_pattern.return_value = ['/test/file.pdf']
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()

    def test_cli_with_update_dates(self):
        """Test CLI with update-dates flag."""
        with patch('sys.argv', ['tax-document-lister', '--update-dates']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                
                with self.assertLogs(level='INFO') as log_capture:
                    assert main() == 0
                    
                    # Verify log messages
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Updating YAML with inferred dates" in msg for msg in log_messages)
                    assert any("YAML updated successfully!" in msg for msg in log_messages)
                    
                mock_instance.update_yaml_with_dates.assert_called_once()

    def test_cli_with_base_path(self):
        """Test CLI with base path without verbose flag."""
        with patch('sys.argv', ['tax-document-lister', '--base-path', '/test/path']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.required_patterns = {
                    'banking': [{'pattern': '.*', 'name': 'test'}]
                }
                mock_instance.find_files_matching_pattern.return_value = ['/test/file.pdf']
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()
                mock_checker.assert_called_once_with('/test/path', verbose=False)

    def test_cli_with_base_path_verbose(self):
        """Test CLI with base path and verbose flag."""
        with patch('sys.argv', ['tax-document-lister', '--base-path', '/test/path', '--verbose']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.required_patterns = {
                    'banking': [{'pattern': '.*', 'name': 'test'}]
                }
                mock_instance.find_files_matching_pattern.return_value = ['/test/file.pdf']
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()
                mock_checker.assert_called_once_with('/test/path', verbose=True)

    def test_cli_with_list_missing(self):
        """Test CLI with list-missing flag."""
        with patch('sys.argv', ['tax-document-lister', '--list-missing']):
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
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_missing_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()
                mock_instance.check_year.assert_called_once()

    def test_cli_with_no_years_found(self):
        """Test CLI when no tax years are found in the directory."""
        with patch('sys.argv', ['tax-document-lister', '--base-path', '/empty/path']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = []
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()

    def test_cli_with_verbose_output(self):
        """Test CLI with verbose output for various operations."""
        with patch('sys.argv', ['tax-document-lister', '--verbose']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.required_patterns = {
                    'banking': [{'pattern': '.*', 'name': 'test'}]
                }
                mock_instance.find_files_matching_pattern.return_value = ['/test/file.pdf']
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that list_files was called (output would go to stdout)
                    mock_stdout.write.assert_called()

    def test_cli_with_verbose_update_dates(self):
        """Test CLI with verbose output for update dates operation."""
        with patch('sys.argv', ['tax-document-lister', '--update-dates', '--verbose']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                
                with self.assertLogs(level='DEBUG') as log_capture:
                    assert main() == 0
                    
                    # Verify verbose output
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Updating YAML with inferred dates" in msg for msg in log_messages)
                    assert any("YAML updated successfully!" in msg for msg in log_messages)

    def test_cli_with_json_format(self):
        """Test CLI with JSON output format."""
        with patch('sys.argv', ['tax-document-lister', '--format', 'json', '--list-missing']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
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
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that JSON output was written to stdout
                    mock_stdout.write.assert_called()

    def test_cli_with_csv_format(self):
        """Test CLI with CSV output format."""
        with patch('sys.argv', ['tax-document-lister', '--format', 'csv', '--list-missing']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
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
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that CSV output was written to stdout
                    mock_stdout.write.assert_called()

    def test_cli_default_format(self):
        """Test CLI with default output format."""
        with patch('sys.argv', ['tax-document-lister', '--list-missing']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
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
                
                with patch('sys.stdout') as mock_stdout:
                    assert main() == 0
                    # Verify that output was written to stdout
                    mock_stdout.write.assert_called() 
