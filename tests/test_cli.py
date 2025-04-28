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
        with patch('sys.argv', ['tax-document-lister', '--year', '2023', '--no-list']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.check_year.return_value = True
                
                with self.assertLogs(level='INFO') as log_capture:
                    assert main() == 0
                    
                    # Verify log messages
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Checking documents for year 2023" in msg for msg in log_messages)
                    
                mock_instance.check_year.assert_called_once_with('2023')

    def test_cli_with_update_dates(self):
        """Test CLI with update-dates flag."""
        with patch('sys.argv', ['tax-document-lister', '--update-dates', '--no-list']):
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
        with patch('sys.argv', ['tax-document-lister', '--base-path', '/test/path', '--no-list']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = True
                
                with self.assertLogs(level='INFO') as log_capture:
                    assert main() == 0
                    
                    # Verify log messages
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Listing available tax years" in msg for msg in log_messages)
                    assert any("Found 1 tax years: 2023" in msg for msg in log_messages)
                    
                mock_checker.assert_called_once_with('/test/path', verbose=False)

    def test_cli_with_base_path_verbose(self):
        """Test CLI with base path and verbose flag."""
        with patch('sys.argv', ['tax-document-lister', '--base-path', '/test/path', '--verbose', '--no-list']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = True
                
                with self.assertLogs(level='DEBUG') as log_capture:
                    assert main() == 0
                    
                    # Verify log messages
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Base path: /test/path" in msg for msg in log_messages)
                    assert any("Listing available tax years" in msg for msg in log_messages)
                    assert any("Found 1 tax years: 2023" in msg for msg in log_messages)
                    
                mock_checker.assert_called_once_with('/test/path', verbose=True)

    def test_cli_with_failed_check(self):
        """Test CLI with failed document check."""
        with patch('sys.argv', ['tax-document-lister', '--year', '2023', '--no-list']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.check_year.return_value = False
                
                with self.assertLogs(level='INFO') as log_capture:
                    assert main() == 1
                    
                    # Verify log messages
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Checking documents for year 2023" in msg for msg in log_messages)

    def test_cli_with_no_years(self):
        """Test CLI when no arguments are provided - should show help message."""
        with patch('sys.argv', ['tax-document-lister']):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.side_effect = SystemExit(0)  # Simulate argparse's help behavior
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

    def test_cli_with_no_years_found(self):
        """Test CLI when no tax years are found in the directory."""
        with patch('sys.argv', ['tax-document-lister', '--base-path', '/empty/path', '--no-list']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = []
                
                with self.assertLogs(level='ERROR') as log_capture:
                    result = main()
                    
                    # Verify that the appropriate message was logged
                    assert any("No tax years found in the directory!" in record.message 
                             for record in log_capture.records)
                    
                    # Verify that the function returned 1 (error)
                    assert result == 1

    def test_cli_with_verbose_output(self):
        """Test CLI with verbose output for various operations."""
        with patch('sys.argv', ['tax-document-lister', '--verbose', '--no-list']):
            with patch('tax_assistant.cli.TaxDocumentChecker') as mock_checker:
                mock_instance = MagicMock()
                mock_checker.return_value = mock_instance
                mock_instance.list_available_years.return_value = ['2023']
                mock_instance.check_year.return_value = True
                
                with self.assertLogs(level='DEBUG') as log_capture:
                    assert main() == 0
                    
                    # Verify verbose output
                    log_messages = [record.message for record in log_capture.records]
                    assert any("Initializing TaxDocumentChecker" in msg for msg in log_messages)
                    assert any("Base path: ." in msg for msg in log_messages)
                    assert any("Listing available tax years" in msg for msg in log_messages)
                    assert any("Found 1 tax years: 2023" in msg for msg in log_messages)
                    assert any("Checking documents for all available years" in msg for msg in log_messages)
                    assert any("Processing year 2023" in msg for msg in log_messages)
                    assert any("Document check complete!" in msg for msg in log_messages)

    def test_cli_with_verbose_update_dates(self):
        """Test CLI with verbose output for update dates operation."""
        with patch('sys.argv', ['tax-document-lister', '--update-dates', '--verbose', '--no-list']):
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
        with patch('sys.argv', ['tax-document-lister', '--format', 'json']):
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
                    # Verify that JSON output was written to stdout
                    mock_stdout.write.assert_called()

    def test_cli_with_csv_format(self):
        """Test CLI with CSV output format."""
        with patch('sys.argv', ['tax-document-lister', '--format', 'csv']):
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
                    # Verify that CSV output was written to stdout
                    mock_stdout.write.assert_called() 
