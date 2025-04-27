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
    """Test CLI with base path without verbose flag."""
    with patch('sys.argv', ['tax-document-checker', '--base-path', '/test/path']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.list_available_years.return_value = ['2023']
            mock_instance.check_year.return_value = True
            
            assert main() == 0
            mock_checker.assert_called_once_with('/test/path', verbose=False)

def test_cli_with_base_path_verbose():
    """Test CLI with base path and verbose flag."""
    with patch('sys.argv', ['tax-document-checker', '--base-path', '/test/path', '--verbose']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.list_available_years.return_value = ['2023']
            mock_instance.check_year.return_value = True
            
            assert main() == 0
            mock_checker.assert_called_once_with('/test/path', verbose=True)

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

def test_cli_with_no_years_found():
    """Test CLI when no tax years are found in the directory."""
    with patch('sys.argv', ['tax-document-checker']):
        with patch('argparse.ArgumentParser.parse_args') as mock_args:
            mock_args.return_value = MagicMock(year=None, update_dates=False, base_path='/empty/path')
            
            # Mock TaxDocumentChecker to return no years
            with patch('tax_document_checker.checker.TaxDocumentChecker') as mock_checker_class:
                mock_checker = MagicMock()
                mock_checker_class.return_value = mock_checker
                mock_checker.list_available_years.return_value = []
                
                with patch('builtins.print') as mock_print:
                    from tax_document_checker.cli import main
                    result = main()
                    
                    # Verify that the appropriate message was printed
                    mock_print.assert_called_with("No tax years found in the directory!")
                    
                    # Verify that the function returned 1 (error)
                    assert result == 1 

def test_cli_with_verbose_output():
    """Test CLI with verbose output for various operations."""
    with patch('sys.argv', ['tax-document-checker', '--verbose']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            mock_instance.list_available_years.return_value = ['2023']
            mock_instance.check_year.return_value = True
            
            with patch('builtins.print') as mock_print:
                assert main() == 0
                
                # Verify verbose output
                mock_print.assert_any_call("Initializing TaxDocumentChecker...")
                mock_print.assert_any_call("Base path: .")
                mock_print.assert_any_call("\nListing available tax years...")
                mock_print.assert_any_call("Found 1 tax years: 2023")
                mock_print.assert_any_call("\nChecking documents for all available years...")
                mock_print.assert_any_call("\nProcessing year 2023...")
                mock_print.assert_any_call("\nDocument check complete!")

def test_cli_with_verbose_update_dates():
    """Test CLI with verbose output for update dates operation."""
    with patch('sys.argv', ['tax-document-checker', '--update-dates', '--verbose']):
        with patch('tax_document_checker.cli.TaxDocumentChecker') as mock_checker:
            mock_instance = MagicMock()
            mock_checker.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                assert main() == 0
                
                # Verify verbose output
                mock_print.assert_any_call("Initializing TaxDocumentChecker...")
                mock_print.assert_any_call("\nUpdating YAML with inferred dates...")
                mock_print.assert_any_call("YAML updated successfully!") 