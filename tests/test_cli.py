import pytest
from unittest.mock import patch, MagicMock
from tax_document_checker.cli import main
import sys

def test_cli_with_year():
    with patch('sys.argv', ['tax-document-checker', '--year', '2023']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.check_year.return_value = True
            
            assert main() == 0
            mock_instance.check_year.assert_called_once_with('2023')

def test_cli_with_update_dates():
    with patch('sys.argv', ['tax-document-checker', '--update-dates']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            
            assert main() == 0
            mock_instance.update_yaml_with_dates.assert_called_once()

def test_cli_with_base_path():
    with patch('sys.argv', ['tax-document-checker', '--base-path', '/test/path']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.list_available_years.return_value = ['2023']
            mock_instance.check_year.return_value = True
            
            assert main() == 0
            mock_checker.assert_called_once_with('/test/path')

def test_cli_with_failed_check():
    with patch('sys.argv', ['tax-document-checker', '--year', '2023']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.check_year.return_value = False
            
            assert main() == 1

def test_cli_with_no_years():
    with patch('sys.argv', ['tax-document-checker']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.list_available_years.return_value = []
            
            assert main() == 1 