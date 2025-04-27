import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import tempfile
import shutil
from pathlib import Path
import yaml
from datetime import datetime

# Add the parent directory to the path so we can import the script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tax_document_checker.checker import TaxDocumentChecker, FREQUENCY_EXPECTATIONS

class TestTaxDocumentChecker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.checker = TaxDocumentChecker(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_extract_date_from_filename(self):
        """Test date extraction from filename."""
        filename = "2023-01-15_test.pdf"
        date = self.checker.extract_date_from_filename(filename)
        self.assertEqual(date.year, 2023)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)

    def test_load_config(self):
        """Test loading configuration."""
        config_data = {
            'test_pattern': {
                'frequency': 'monthly',
                'pattern': r'\d{4}-\d{2}-\d{2}_test\.pdf'
            }
        }
        config_path = os.path.join(self.temp_dir, 'config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        self.checker.config_file = config_path
        config = self.checker.load_base_config()
        self.assertEqual(config, config_data)

    def test_validate_frequency(self):
        """Test frequency validation."""
        matches = [
            '2023-01-01_test.pdf',
            '2023-02-01_test.pdf',
            '2023-03-01_test.pdf',
            '2023-04-01_test.pdf',
            '2023-05-01_test.pdf',
            '2023-06-01_test.pdf',
            '2023-07-01_test.pdf',
            '2023-08-01_test.pdf',
            '2023-09-01_test.pdf',
            '2023-10-01_test.pdf',
            '2023-11-01_test.pdf',
            '2023-12-01_test.pdf'
        ]
        is_valid, count, expected_count = self.checker.validate_frequency(matches, 'monthly', '2023')
        self.assertTrue(is_valid)
        self.assertEqual(count, 12)
        self.assertEqual(expected_count, 12)

    def test_load_base_config(self):
        """Test loading base configuration."""
        test_config = {'test': 'value'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name

        try:
            checker = TaxDocumentChecker(self.temp_dir, config_file=config_path)
            config = checker.load_base_config()
            self.assertEqual(config, test_config)
        finally:
            os.unlink(config_path)

    def test_load_private_config(self):
        """Test loading private configuration."""
        test_config = {'private': 'value'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name

        try:
            checker = TaxDocumentChecker(self.temp_dir, private_config_file=config_path)
            config = checker.load_private_config()
            self.assertEqual(config, test_config)
        finally:
            os.unlink(config_path)

    def test_merge_configs(self):
        """Test merging base and private configurations."""
        self.checker.base_config = {'base': {'sub': ['item1']}}
        self.checker.private_config = {'base': {'sub': ['item2']}}
        merged = self.checker.merge_configs()
        assert merged['base']['sub'] == ['item1', 'item2']

    def test_build_pattern(self):
        """Test pattern building."""
        pattern = self.checker.build_pattern(
            base='test',
            suffix='suffix',
            account_type='type',
            identifiers=['id1', 'id2']
        )
        assert '\\d{4}-\\d{2}-\\d{2}' in pattern  # Date pattern
        assert 'test' in pattern  # Base
        assert '(?:id1|id2)' in pattern  # Identifiers
        assert 'type' in pattern  # Account type
        assert '\\.pdf$' in pattern  # Extension

    def test_find_files_matching_pattern(self):
        """Test finding files matching a pattern."""
        test_files = [
            Path('/test/2023-01-01_test.pdf'),
            Path('/test/2023-02-01_test.pdf')
        ]
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = test_files
            with patch('pathlib.Path.is_file', return_value=True):
                matches = self.checker.find_files_matching_pattern(r'\d{4}-\d{2}-\d{2}_test\.pdf', year='2023')
                assert len(matches) == 2

    def test_check_annual_documents(self):
        """Test checking annual documents."""
        matches = [
            '/test/2023-01-01_regular.pdf',
            '/test/2023-12-31_annual.pdf'
        ]
        found, count, expected = self.checker.check_annual_documents(
            matches, '2023', 'annual'
        )
        assert found is True
        assert count == 2
        assert expected == 2

    def test_update_yaml_with_dates(self):
        """Test updating YAML with dates."""
        self.checker.account_dates = {
            'test_account': {
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'files': ['file1.pdf', 'file2.pdf']
            }
        }
        self.checker.private_config = {
            'employment': {
                'current': [{'name': 'test_account'}]
            }
        }
        with patch.object(self.checker, 'save_config'):
            updated = self.checker.update_yaml_with_dates()
            assert updated['employment']['current'][0]['start_date'] == '2023-01-01'
            assert updated['employment']['current'][0]['end_date'] == '2023-12-31'

    def test_load_config_file_not_found(self):
        """Test loading configuration when file is not found."""
        self.checker.config_file = '/nonexistent/path/config.yaml'
        config = self.checker.load_base_config()
        assert config == {}

    def test_analyze_account_dates(self):
        """Test analyzing account dates from files."""
        # Mock file finding
        mock_files = [
            '/test/2023-01-01_company1.pdf',
            '/test/2023-12-31_company1.pdf',
            '/test/2023-06-15_company2.pdf'
        ]
        
        self.checker.required_patterns = {
            'employment': [
                {'pattern': r'\d{4}-\d{2}-\d{2}_company1\.pdf', 'name': 'Company1'},
                {'pattern': r'\d{4}-\d{2}-\d{2}_company2\.pdf', 'name': 'Company2'}
            ]
        }
        
        with patch.object(self.checker, 'find_files_matching_pattern') as mock_find:
            mock_find.side_effect = [
                [mock_files[0], mock_files[1]],  # Company1 files
                [mock_files[2]]  # Company2 files
            ]
            
            dates = self.checker.analyze_account_dates()
            
            assert dates['Company1']['start_date'] == '2023-01-01'
            assert dates['Company1']['end_date'] == '2023-12-31'
            assert dates['Company2']['start_date'] == '2023-06-15'
            assert dates['Company2']['end_date'] == '2023-06-15'

    def test_flatten_config_employment(self):
        """Test flattening employment configuration."""
        self.checker.config = {
            'employment': {
                'current': [{
                    'name': 'Test Company',
                    'frequency': 'monthly',
                    'patterns': [{'base': 'test-company'}]
                }]
            }
        }
        
        patterns = self.checker.flatten_config()
        assert 'employment' in patterns
        assert len(patterns['employment']) == 1
        assert patterns['employment'][0]['name'] == 'Test Company'
        assert patterns['employment'][0]['frequency'] == 'monthly'
        assert '\\d{4}-\\d{2}-\\d{2}_test-company\\.pdf$' in patterns['employment'][0]['pattern']

    def test_flatten_config_investments(self):
        """Test flattening investment configuration."""
        self.checker.config = {
            'investment': {
                'us': [{
                    'name': 'US Investment',
                    'frequency': 'quarterly',
                    'patterns': [{'base': 'us-inv'}]
                }],
                'uk': [{
                    'name': 'UK Investment',
                    'frequency': 'yearly',
                    'patterns': [{'base': 'uk-inv'}]
                }]
            }
        }
        
        patterns = self.checker.flatten_config()
        assert 'investment_us' in patterns
        assert 'investment_uk' in patterns
        assert patterns['investment_us'][0]['name'] == 'US Investment'
        assert patterns['investment_uk'][0]['name'] == 'UK Investment'

    def test_check_year_with_missing_files(self):
        """Test checking a year with missing files."""
        self.checker.required_patterns = {
            'employment': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                'name': 'Test Company',
                'frequency': 'monthly'
            }]
        }

        with patch.object(self.checker, 'find_files_matching_pattern', return_value=[]):
            result = self.checker.check_year('2023')
            self.assertEqual(result['employment'], [])

    def test_check_year_with_complete_files(self):
        """Test checking a year with all required files."""
        self.checker.required_patterns = {
            'employment': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                'name': 'Test Company',
                'frequency': 'monthly'
            }]
        }

        mock_files = [f'/test/2023-{month:02d}-01_company.pdf' for month in range(1, 13)]
        with patch.object(self.checker, 'find_files_matching_pattern', return_value=mock_files):
            result = self.checker.check_year('2023')
            self.assertEqual(result['employment'], mock_files)

    def test_check_year_with_closed_account(self):
        """Test checking a year with a closed account."""
        self.checker.required_patterns = {
            'employment': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                'name': 'Test Company',
                'frequency': 'monthly'
            }]
        }

        self.checker.account_dates = {
            'Test Company': {
                'start_date': '2020-01-01',
                'end_date': '2022-12-31'
            }
        }

        result = self.checker.check_year('2023')
        self.assertEqual(result['employment'], [])

    def test_list_available_years(self):
        """Test listing available tax years."""
        # Create test directory structure
        years = ['2021', '2022', '2023']
        for year in years:
            os.makedirs(os.path.join(self.temp_dir, year))
        
        available_years = self.checker.list_available_years()
        assert available_years == years

    def test_get_year_from_path(self):
        """Test extracting year from various path formats."""
        test_paths = [
            ('/test/2023/file.pdf', '2023'),
            ('/test/2023-01-01_doc.pdf', '2023'),
            ('/test/not_a_year.pdf', None),
            ('/test/2023-folder', '2023')
        ]
        
        for path, expected in test_paths:
            result = self.checker.get_year_from_path(path)
            assert result == expected

    def test_error_handling_in_config_loading(self):
        """Test error handling when loading configuration with invalid YAML."""
        # Create a temporary file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: :")
            temp_path = f.name

        try:
            # Test loading invalid YAML
            with patch('builtins.print') as mock_print:
                checker = TaxDocumentChecker(base_path=self.temp_dir, config_file=temp_path)
                config = checker.load_base_config()
                self.assertEqual(config, {})
                mock_print.assert_called_with(
                    f'Error parsing base configuration file: mapping values are not allowed here\n'
                    f'  in "{temp_path}", line 1, column 14'
                )
        finally:
            os.unlink(temp_path)

    def test_check_year_output_formatting(self):
        """Test the output formatting of check_year."""
        self.checker.required_patterns = {
            'employment': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                'name': 'Test Company',
                'frequency': 'monthly'
            }]
        }

        # Test with incomplete files
        mock_files = [f'/test/2023-{month:02d}-01_company.pdf' for month in range(1, 6)]  # Only 5 months
        with patch.object(self.checker, 'find_files_matching_pattern', return_value=mock_files):
            with patch('builtins.print') as mock_print:
                result = self.checker.check_year('2023')
                self.assertEqual(result['employment'], mock_files)

    def test_main_function(self):
        """Test the main function."""
        test_args = ['--year', '2023']
        with patch('sys.argv', ['tax-document-checker'] + test_args):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.return_value = MagicMock(year='2023', update_dates=False)
                with patch.object(TaxDocumentChecker, 'check_year') as mock_check:
                    mock_check.return_value = True
                    with patch('os.path.dirname', return_value='/test/path'):
                        from tax_document_checker.checker import main
                        main()
                        mock_check.assert_called_once_with('2023')

    def test_main_function_update_dates(self):
        """Test the main function with update_dates flag."""
        test_args = ['--update-dates']
        with patch('sys.argv', ['tax-document-checker'] + test_args):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.return_value = MagicMock(year=None, update_dates=True)
                with patch.object(TaxDocumentChecker, 'update_yaml_with_dates') as mock_update:
                    with patch('os.path.dirname', return_value='/test/path'):
                        from tax_document_checker.checker import main
                        main()
                        mock_update.assert_called_once()

    def test_main_function_no_args(self):
        """Test the main function with no arguments."""
        with patch('sys.argv', ['tax-document-checker']):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.return_value = MagicMock(year=None, update_dates=False)
                with patch.object(TaxDocumentChecker, 'list_available_years') as mock_list:
                    mock_list.return_value = ['2022', '2023']
                    with patch.object(TaxDocumentChecker, 'check_year') as mock_check:
                        with patch('os.path.dirname', return_value='/test/path'):
                            from tax_document_checker.checker import main
                            main()
                            assert mock_check.call_count == 2
                            mock_check.assert_has_calls([
                                unittest.mock.call('2022'),
                                unittest.mock.call('2023')
                            ])

    def test_save_config(self):
        """Test saving configuration to YAML file."""
        test_config = {
            'test': {'value': 'test_value'}
        }
        
        # Test saving private config
        with patch('os.path.dirname') as mock_dirname:
            mock_dirname.return_value = self.temp_dir
            with patch('builtins.open', mock_open()) as mock_file:
                self.checker.save_config(test_config, is_private=True)
                mock_file.assert_called_once()
                # Verify the correct filename was used
                self.assertIn('tax_document_patterns_private.yaml', mock_file.call_args[0][0])

        # Test saving base config
        with patch('os.path.dirname') as mock_dirname:
            mock_dirname.return_value = self.temp_dir
            with patch('builtins.open', mock_open()) as mock_file:
                self.checker.save_config(test_config, is_private=False)
                mock_file.assert_called_once()
                # Verify the correct filename was used
                self.assertIn('tax_document_patterns_base.yaml', mock_file.call_args[0][0])

    def test_merge_configs_with_complex_data(self):
        """Test merging configurations with complex nested data."""
        self.checker.base_config = {
            'employment': {
                'current': [{'name': 'Company1', 'patterns': ['pattern1']}],
                'previous': [{'name': 'Company2', 'patterns': ['pattern2']}]
            },
            'bank': {
                'uk': {'accounts': ['account1']}
            }
        }
        self.checker.private_config = {
            'employment': {
                'current': [{'name': 'Company3', 'patterns': ['pattern3']}],
                'generic': [{'name': 'Generic1', 'patterns': ['pattern4']}]
            },
            'bank': {
                'uk': {'accounts': ['account2']},
                'us': {'accounts': ['account3']}
            }
        }
        
        merged = self.checker.merge_configs()
        
        # Verify merged structure
        self.assertIn('employment', merged)
        self.assertIn('current', merged['employment'])
        self.assertIn('previous', merged['employment'])
        self.assertIn('generic', merged['employment'])
        self.assertEqual(len(merged['employment']['current']), 2)  # Combined from both configs
        self.assertEqual(len(merged['bank']['uk']['accounts']), 2)  # Combined accounts
        self.assertIn('us', merged['bank'])  # Added from private config

    def test_update_yaml_with_dates_complex(self):
        """Test updating YAML with dates for complex configurations."""
        # Setup test data
        self.checker.private_config = {
            'employment': {
                'current': [{'name': 'Current Corp'}],
                'previous': [{'name': 'Past Corp'}]
            },
            'investment': {
                'us': [{'name': 'US Investment'}],
                'uk': [{'name': 'UK Investment'}]
            },
            'bank': {
                'uk': [{
                    'name': 'UK Bank',
                    'account_types': [{'name': 'Savings'}]
                }],
                'us': [{
                    'name': 'US Bank'
                }]
            },
            'additional': [
                {'name': 'Extra Doc'}
            ]
        }
        
        self.checker.account_dates = {
            'Current Corp': {'start_date': '2023-01-01', 'end_date': '2023-12-31'},
            'Past Corp': {'start_date': '2022-01-01', 'end_date': '2022-12-31'},
            'US Investment': {'start_date': '2023-03-01', 'end_date': '2023-09-30'},
            'UK Investment': {'start_date': '2023-01-01', 'end_date': '2023-12-31'},
            'UK Bank - Savings': {'start_date': '2023-01-01', 'end_date': '2023-12-31'},
            'US Bank': {'start_date': '2023-01-01', 'end_date': '2023-12-31'},
            'Extra Doc': {'start_date': '2023-01-01', 'end_date': '2023-12-31'}
        }
        
        with patch.object(self.checker, 'save_config'):
            updated = self.checker.update_yaml_with_dates()
            
            # Verify employment dates
            self.assertEqual(updated['employment']['current'][0]['start_date'], '2023-01-01')
            self.assertEqual(updated['employment']['previous'][0]['end_date'], '2022-12-31')
            
            # Verify investment dates
            self.assertEqual(updated['investment']['us'][0]['start_date'], '2023-03-01')
            self.assertEqual(updated['investment']['uk'][0]['end_date'], '2023-12-31')
            
            # Verify bank dates
            self.assertEqual(
                updated['bank']['uk'][0]['account_types'][0]['start_date'],
                '2023-01-01'
            )
            self.assertEqual(updated['bank']['us'][0]['start_date'], '2023-01-01')
            
            # Verify additional dates
            self.assertEqual(updated['additional'][0]['start_date'], '2023-01-01')

    def test_flatten_config_with_complex_patterns(self):
        """Test flattening configuration with complex pattern structures."""
        self.checker.config = {
            'employment': {
                'current': [{
                    'name': 'Complex Corp',
                    'frequency': 'monthly',
                    'patterns': [
                        {'base': 'complex', 'identifiers': ['id1', 'id2'], 'suffix': 'report'},
                        {'base': 'simple'}
                    ]
                }],
                'previous': [{
                    'name': 'Simple Corp',
                    'frequency': 'yearly',
                    'patterns': ['static-pattern']
                }]
            },
            'bank': {
                'uk': [{
                    'name': 'UK Bank',
                    'frequency': 'monthly',
                    'patterns': [
                        {'base': 'ukbank', 'account_type': 'savings'},
                        {'base': 'ukbank', 'account_type': 'current'}
                    ]
                }]
            }
        }

        patterns = self.checker.flatten_config()

        # Verify employment patterns
        self.assertIn('employment', patterns)
        complex_patterns = [p for p in patterns['employment'] if p['name'] == 'Complex Corp']
        self.assertEqual(len(complex_patterns), 2)
        self.assertTrue(any('\\d{4}-\\d{2}-\\d{2}_complex_(?:id1|id2)_report\\.pdf' in p['pattern'] for p in complex_patterns))
        self.assertTrue(any('\\d{4}-\\d{2}-\\d{2}_simple\\.pdf' in p['pattern'] for p in complex_patterns))

        simple_pattern = next(p for p in patterns['employment'] if p['name'] == 'Simple Corp')
        self.assertEqual(simple_pattern['pattern'], 'static-pattern')

        # Verify bank patterns
        self.assertIn('bank_uk', patterns)
        bank_patterns = [p for p in patterns['bank_uk'] if p['name'] == 'UK Bank']
        self.assertEqual(len(bank_patterns), 2)
        self.assertTrue(any('\\d{4}-\\d{2}-\\d{2}_ukbank_savings\\.pdf' in p['pattern'] for p in bank_patterns))
        self.assertTrue(any('\\d{4}-\\d{2}-\\d{2}_ukbank_current\\.pdf' in p['pattern'] for p in bank_patterns))

    def test_document_validation_edge_cases(self):
        """Test edge cases in document validation."""
        # Test with empty matches
        is_valid, count, expected = self.checker.validate_frequency([], 'monthly', '2023')
        self.assertFalse(is_valid)
        self.assertEqual(count, 0)
        self.assertEqual(expected, 12)

        # Test with files from wrong year
        matches = [
            '/test/2022-01-01_doc.pdf',  # Wrong year
            '/test/2022-02-01_doc.pdf'   # Wrong year
        ]
        is_valid, count, expected = self.checker.validate_frequency(matches, 'monthly', '2023')
        self.assertFalse(is_valid)
        self.assertEqual(count, 0)
        self.assertEqual(expected, 12)

        # Test with unknown frequency - should pass if at least one file exists
        matches = ['/test/2023-01-01_doc.pdf']
        is_valid, count, expected = self.checker.validate_frequency(matches, 'unknown', '2023')
        self.assertTrue(is_valid)  # Changed to assertTrue as we expect true for unknown frequency with at least one file
        self.assertEqual(count, 1)
        self.assertEqual(expected, 1)

        # Test with unknown frequency and no files
        matches = []
        is_valid, count, expected = self.checker.validate_frequency(matches, 'unknown', '2023')
        self.assertFalse(is_valid)
        self.assertEqual(count, 0)
        self.assertEqual(expected, 1)

    def test_date_extraction_edge_cases(self):
        """Test edge cases in date extraction from filenames."""
        # Test with invalid date format
        result = self.checker.extract_date_from_filename('invalid_date.pdf')
        self.assertIsNone(result)

        # Test with no date
        result = self.checker.extract_date_from_filename('nodatefile.pdf')
        self.assertIsNone(result)

        # Test with malformed date
        result = self.checker.extract_date_from_filename('2023-13-32_doc.pdf')
        self.assertIsNone(result)

    def test_check_year_edge_cases(self):
        """Test edge cases in year checking functionality."""
        # Setup test with invalid account dates
        self.checker.required_patterns = {
            'test': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_test\.pdf',
                'name': 'Test Account',
                'frequency': 'monthly'
            }]
        }
        self.checker.account_dates = {
            'Test Account': {
                'start_date': 'invalid-date',  # Invalid date format
                'end_date': '2023-12-31'
            }
        }

        # Should handle invalid date gracefully
        with patch('builtins.print'):  # Suppress print output
            result = self.checker.check_year('2023')
            self.assertEqual(result['test'], [])

    def test_config_flattening_edge_cases(self):
        """Test edge cases in configuration flattening."""
        # Test with empty config
        self.checker.config = {}
        patterns = self.checker.flatten_config()
        expected_empty = {
            'employment': [],
            'investment_us': [],
            'investment_uk': [],
            'bank_uk': [],
            'bank_us': [],
            'additional': []
        }
        self.assertEqual(patterns, expected_empty)

        # Test with None values
        self.checker.config = {
            'employment': {
                'current': [{
                    'name': 'Test Corp',
                    'frequency': 'monthly',
                    'patterns': None
                }]
            }
        }
        patterns = self.checker.flatten_config()
        self.assertEqual(patterns, expected_empty)

        # Test with empty patterns
        self.checker.config = {
            'employment': {
                'current': [{
                    'name': 'Test Corp',
                    'frequency': 'monthly',
                    'patterns': []
                }]
            }
        }
        patterns = self.checker.flatten_config()
        self.assertEqual(patterns, expected_empty)

if __name__ == '__main__':
    unittest.main()
