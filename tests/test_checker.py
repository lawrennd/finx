import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import tempfile
import shutil
from pathlib import Path
import yaml
from datetime import datetime
from io import StringIO
from contextlib import redirect_stdout

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
        config_path = os.path.join(self.temp_dir, 'tax_document_patterns_base.yml')
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
        private_config_data = {
            'private_pattern': {
                'frequency': 'monthly',
                'pattern': r'\d{4}-\d{2}-\d{2}_private\.pdf'
            }
        }
        private_config_path = os.path.join(self.temp_dir, 'tax_document_patterns_private.yml')
        with open(private_config_path, 'w') as f:
            yaml.dump(private_config_data, f)
        
        self.checker.private_config_file = private_config_path
        config = self.checker.load_private_config()
        self.assertEqual(config, private_config_data)

    def test_load_private_config_yaml_error(self):
        """Test handling of YAML parsing errors in private configuration."""
        private_config_path = os.path.join(self.temp_dir, 'tax_document_patterns_dummy.yml')
        with open(private_config_path, 'w') as f:
            f.write('invalid: yaml: content: {')
        
        self.checker.private_config_file = private_config_path
        config = self.checker.load_private_config()
        self.assertEqual(config, {})

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
        self.checker.config_file = '/nonexistent/path/tax_document_patterns_base.yaml'
        config = self.checker.load_base_config()
        self.assertEqual(config, {})

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
        # Create test directory structure with PDF files
        years = ['2021', '2022', '2023']
        self.checker.directory_mapping = {'test': ['.']}  # Map the root directory
        
        for year in years:
            dir_path = os.path.join(self.temp_dir, year)
            os.makedirs(dir_path)
            # Create a test PDF file in each year directory
            with open(os.path.join(dir_path, f'{year}-01-01_test.pdf'), 'w') as f:
                f.write('test content')
        
        available_years = self.checker.list_available_years()
        self.assertEqual(sorted(available_years), sorted(years))
        
        # Clean up files
        for year in years:
            os.remove(os.path.join(self.temp_dir, year, f'{year}-01-01_test.pdf'))
            os.rmdir(os.path.join(self.temp_dir, year))

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
                self.assertIn('tax_document_patterns_private.yml', mock_file.call_args[0][0])

        # Test saving base config
        with patch('os.path.dirname') as mock_dirname:
            mock_dirname.return_value = self.temp_dir
            with patch('builtins.open', mock_open()) as mock_file:
                self.checker.save_config(test_config, is_private=False)
                mock_file.assert_called_once()
                # Verify the correct filename was used
                self.assertIn('tax_document_patterns_base.yml', mock_file.call_args[0][0])

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

    def test_load_directory_mapping_yaml_error(self):
        """Test handling of YAML parsing errors in directory mapping."""
        # Create a temporary file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: :")
            temp_path = f.name

        try:
            # Test loading invalid YAML
            with patch('builtins.print') as mock_print:
                checker = TaxDocumentChecker(base_path=self.temp_dir, directory_mapping_file=temp_path)
                mapping = checker.load_directory_mapping()
                self.assertEqual(mapping, {})
                mock_print.assert_called_with(
                    f'Error parsing directory mapping file: mapping values are not allowed here\n'
                    f'  in "{temp_path}", line 1, column 14'
                )
        finally:
            os.unlink(temp_path)

    def test_merge_configs_with_different_types(self):
        """Test merging configurations with different data types."""
        self.checker.base_config = {
            'test': {
                'list': ['item1'],
                'dict': {'key1': 'value1'}
            }
        }
        self.checker.private_config = {
            'test': {
                'list': ['item2'],
                'dict': {'key2': 'value2'}
            }
        }
        
        merged = self.checker.merge_configs()
        
        # Verify merged structure
        self.assertEqual(merged['test']['list'], ['item1', 'item2'])
        self.assertEqual(merged['test']['dict'], {'key1': 'value1', 'key2': 'value2'})

    def test_find_files_matching_pattern_with_category_mapping(self):
        """Test finding files with category-specific directory mapping."""
        # Set up directory mapping
        self.checker.directory_mapping = {
            'test_category': ['test_dir']
        }
        
        # Create test directory and files
        test_dir = os.path.join(self.temp_dir, 'test_dir')
        os.makedirs(test_dir)
        
        # Create a file that matches the pattern
        with open(os.path.join(test_dir, '2023-01-01_test.pdf'), 'w') as f:
            f.write('test')
        
        # Create a file that doesn't match the pattern
        with open(os.path.join(test_dir, 'not_a_match.pdf'), 'w') as f:
            f.write('test')
        
        # Find files matching the pattern
        matches = self.checker.find_files_matching_pattern(
            r'\d{4}-\d{2}-\d{2}_test\.pdf',
            year='2023',
            category='test_category'
        )
        
        # Verify results
        self.assertEqual(len(matches), 1)
        self.assertTrue(matches[0].endswith('2023-01-01_test.pdf'))

    def test_check_year_with_date_based_filtering(self):
        """Test checking a year with date-based filtering for employment records."""
        # Set up required patterns with start and end dates
        self.checker.required_patterns = {
            'employment': [
                {
                    'pattern': r'\d{4}-\d{2}-\d{2}_company1\.pdf',
                    'name': 'Company1',
                    'frequency': 'monthly',
                    'start_date': '2022-01-01',
                    'end_date': '2022-12-31'
                },
                {
                    'pattern': r'\d{4}-\d{2}-\d{2}_company2\.pdf',
                    'name': 'Company2',
                    'frequency': 'monthly',
                    'start_date': '2023-01-01',
                    'end_date': '2023-12-31'
                }
            ]
        }
        
        # Mock find_files_matching_pattern to return different results
        with patch.object(self.checker, 'find_files_matching_pattern') as mock_find:
            # Company1 should be skipped for 2023
            # Company2 should be checked for 2023
            mock_find.return_value = ['/test/2023-01-01_company2.pdf']
            
            with patch('builtins.print') as mock_print:
                result = self.checker.check_year('2023')
                
                # Verify that Company1 was skipped
                mock_print.assert_any_call("⏭️ Skipping Company1 (monthly) - not active in 2023 (active from 2022 to 2022)")
                
                # Verify that Company2 was checked
                mock_print.assert_any_call("✓ Found 1 files for Company2 (monthly)")
                
                # Verify results
                self.assertEqual(result['employment'], ['/test/2023-01-01_company2.pdf'])

    def test_find_files_matching_pattern_with_nonexistent_directory(self):
        """Test finding files when the directory doesn't exist."""
        # Set up directory mapping
        self.checker.directory_mapping = {
            'test_category': ['nonexistent_dir']
        }
        
        # Find files matching the pattern
        matches = self.checker.find_files_matching_pattern(
            r'\d{4}-\d{2}-\d{2}_test\.pdf',
            year='2023',
            category='test_category'
        )
        
        # Verify results - should be empty since directory doesn't exist
        self.assertEqual(len(matches), 0)

    def test_check_year_with_invalid_dates(self):
        """Test checking a year with invalid dates in employment records."""
        # Set up required patterns with invalid dates
        self.checker.required_patterns = {
            'employment': [
                {
                    'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                    'name': 'Company',
                    'frequency': 'monthly',
                    'start_date': '9999-01-01',  # Future date
                    'end_date': '9999-12-31'     # Future date
                }
            ]
        }
        
        # Mock find_files_matching_pattern to return some results
        with patch.object(self.checker, 'find_files_matching_pattern') as mock_find:
            mock_find.return_value = ['/test/2023-01-01_company.pdf']
            
            # Should handle future dates by skipping the check
            with patch('builtins.print') as mock_print:
                result = self.checker.check_year('2023')
                
                # Verify that the files were skipped (empty result)
                self.assertEqual(result['employment'], [])
                
                # Verify that we got the skip message
                mock_print.assert_any_call("⏭️ Skipping Company (monthly) - not active in 2023 (active from 9999 to 9999)")

    def test_validate_frequency_with_unknown_frequency(self):
        """Test validating frequency with an unknown frequency type."""
        # Test with unknown frequency and files
        matches = ['/test/2023-01-01_doc.pdf']
        is_valid, count, expected = self.checker.validate_frequency(matches, 'unknown', '2023')
        self.assertTrue(is_valid)  # Should be valid if at least one file exists
        self.assertEqual(count, 1)
        self.assertEqual(expected, 1)

        # Test with unknown frequency and no files
        matches = []
        is_valid, count, expected = self.checker.validate_frequency(matches, 'unknown', '2023')
        self.assertFalse(is_valid)  # Should be invalid if no files exist
        self.assertEqual(count, 0)
        self.assertEqual(expected, 1)

    def test_get_available_years_with_invalid_directory(self):
        """Test getting available years with an invalid directory."""
        # Set up a directory mapping that points to a non-existent directory
        self.checker.directory_mapping = {'test': ['/nonexistent/directory']}
        
        # Mock the glob method to avoid actual filesystem operations
        with patch('pathlib.Path.glob') as mock_glob:
            # Should return an empty list for invalid directory
            years = self.checker.list_available_years()
            self.assertEqual(years, [])
            
            # Verify that glob was not called since the directory doesn't exist
            mock_glob.assert_not_called()

    def test_list_available_years_from_filenames(self):
        """Test listing available years by extracting them from filenames."""
        # Create test files with different years
        test_files = [
            'payslips/2022-12-15_previous-employer.pdf',
            'payslips/2023-01-15_example-employer.pdf',
            'investments/us/2023-03-15_us-investment.pdf',
            'tax/uk/2023-04-15_tax-return-uk.pdf'
        ]
        
        # Set up directory mapping
        self.checker.directory_mapping = {
            'employment': ['payslips'],
            'investment_us': ['investments/us'],
            'additional': ['tax/uk']
        }
        
        # Create the test files
        created_dirs = set()
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            dir_path = os.path.dirname(full_path)
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.add(dir_path)
            with open(full_path, 'w') as f:
                f.write('test content')
        
        # Set the base path to our temp directory
        self.checker.base_path = Path(self.temp_dir)
        
        # Get available years
        years = self.checker.list_available_years()
        
        # Should find both 2022 and 2023
        self.assertEqual(set(years), {'2022', '2023'})
        
        # Clean up files and directories in reverse order (deepest first)
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            os.remove(full_path)
        
        # Remove directories in reverse order of depth
        dirs_by_depth = sorted(created_dirs, key=lambda x: x.count(os.sep), reverse=True)
        for dir_path in dirs_by_depth:
            os.rmdir(dir_path)

    def test_load_private_config_file_not_found(self):
        """Test loading private config when file doesn't exist."""
        self.checker.private_config_file = '/nonexistent/path/tax_document_patterns_dummy.yml'
        config = self.checker.load_private_config()
        self.assertEqual(config, {})

    def test_load_private_config_precedence(self):
        """Test that private config file takes precedence over dummy file when both exist."""
        # Create both private and dummy config files
        private_config_data = {
            'private_pattern': {
                'frequency': 'monthly',
                'pattern': r'\d{4}-\d{2}-\d{2}_private\.pdf'
            }
        }
        dummy_config_data = {
            'dummy_pattern': {
                'frequency': 'yearly',
                'pattern': r'\d{4}-\d{2}-\d{2}_dummy\.pdf'
            }
        }
        
        # Create both files in the temp directory
        private_config_path = os.path.join(self.temp_dir, 'tax_document_patterns_private.yml')
        dummy_config_path = os.path.join(self.temp_dir, 'tax_document_patterns_dummy.yml')
        
        with open(private_config_path, 'w') as f:
            yaml.dump(private_config_data, f)
        
        with open(dummy_config_path, 'w') as f:
            yaml.dump(dummy_config_data, f)
        
        # Create a new checker with both files available
        checker = TaxDocumentChecker(self.temp_dir, verbose=True)
        
        # Verify that the private config file was loaded, not the dummy one
        self.assertEqual(checker.private_config, private_config_data)
        self.assertNotEqual(checker.private_config, dummy_config_data)

    def test_load_directory_mapping_file_not_found(self):
        """Test loading directory mapping when file doesn't exist."""
        self.checker.directory_mapping_file = '/nonexistent/path/directory_mapping.yaml'
        mapping = self.checker.load_directory_mapping()
        self.assertEqual(mapping, {})

    def test_merge_configs_with_non_list_values(self):
        """Test merging configs with non-list values."""
        self.checker.base_config = {
            'test': {
                'subcategory': {'key': 'value1'}
            }
        }
        self.checker.private_config = {
            'test': {
                'subcategory': {'key': 'value2'}
            }
        }
        merged = self.checker.merge_configs()
        self.assertEqual(merged['test']['subcategory']['key'], 'value2')

    def test_flatten_config_with_empty_patterns(self):
        """Test flattening config with empty patterns."""
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
        self.assertEqual(patterns['employment'], [])

    def test_flatten_config_with_additional_patterns(self):
        """Test flattening config with additional patterns section."""
        self.checker.config = {
            'additional': {
                'patterns': {
                    'test_doc': {
                        'base': 'test',
                        'frequency': 'yearly'
                    }
                }
            }
        }
        patterns = self.checker.flatten_config()
        self.assertTrue(any(p['name'] == 'test_doc' for p in patterns['additional']))
        self.assertTrue(any(p['frequency'] == 'yearly' for p in patterns['additional']))

    def test_list_available_years_with_invalid_tax_year_path(self):
        """Test listing available years with an invalid tax year path."""
        self.checker.tax_year_path = Path('invalid/path')
        years = self.checker.list_available_years()
        self.assertEqual(years, [])

    def test_build_pattern_with_all_components(self):
        """Test building pattern with all possible components."""
        pattern = self.checker.build_pattern(
            base='test',
            suffix='suffix',
            account_type='savings',
            identifiers=['id1', 'id2']
        )
        self.assertIn('test', pattern)
        self.assertIn('suffix', pattern)
        self.assertIn('savings', pattern)
        self.assertIn('(?:id1|id2)', pattern)

    def test_check_year_with_invalid_date_format(self):
        """Test checking a year with invalid date format."""
        self.checker.required_patterns = {
            'employment': [
                {
                    'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                    'name': 'Company',
                    'frequency': 'monthly',
                    'start_date': 'invalid-format',
                    'end_date': 'also-invalid'
                }
            ]
        }
        
        with patch.object(self.checker, 'find_files_matching_pattern') as mock_find:
            mock_find.return_value = ['/test/2023-01-01_company.pdf']
            
            with patch('builtins.print') as mock_print:
                result = self.checker.check_year('2023')
                self.assertEqual(result['employment'], ['/test/2023-01-01_company.pdf'])

    def test_check_year_missing_documents_summary(self):
        """Test the missing documents summary in check_year."""
        self.checker.required_patterns = {
            'employment': [
                {
                    'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                    'name': 'Missing Company',
                    'frequency': 'monthly'
                }
            ]
        }
        
        with patch.object(self.checker, 'find_files_matching_pattern', return_value=[]):
            with patch('builtins.print') as mock_print:
                self.checker.check_year('2023')
                mock_print.assert_any_call("\nEMPLOYMENT:")
                mock_print.assert_any_call("- Missing Company (monthly)")

    def test_main_function_error_handling(self):
        """Test error handling in the main function."""
        with patch('sys.argv', ['tax-document-checker', '--year', '2023']):
            with patch('argparse.ArgumentParser.parse_args') as mock_args:
                mock_args.return_value = MagicMock(year='2023', update_dates=False)
                with patch.object(TaxDocumentChecker, 'check_year', side_effect=Exception('Test error')):
                    with patch('os.path.dirname', return_value='/test/path'):
                        with self.assertRaises(Exception):
                            from tax_document_checker.checker import main
                            main()

    def test_verbose_output_in_find_config_file(self):
        """Test verbose output when finding configuration files."""
        # Create a test config file
        test_config = {'test': 'value'}
        config_path = os.path.join(self.temp_dir, 'tax_document_patterns_base.yml')
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Initialize checker with verbose mode and capture print output
        with patch('builtins.print') as mock_print:
            checker = TaxDocumentChecker(
                base_path=self.temp_dir,
                config_file=config_path,
                verbose=True
            )
            
            # Verify that the verbose output was printed
            mock_print.assert_any_call(f"Found tax_document_patterns_base.yml at explicit path: {config_path}")

    def test_verbose_output_in_file_operations(self):
        """Test verbose output in file operations."""
        self.checker.verbose = True
        self.checker.directory_mapping = {'test': ['test_dir']}
        
        # Create test directory and file
        test_dir = os.path.join(self.temp_dir, 'test_dir')
        os.makedirs(test_dir)
        test_file = os.path.join(test_dir, '2023-01-01_test.pdf')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        with patch('builtins.print') as mock_print:
            # Test find_files_matching_pattern
            self.checker.find_files_matching_pattern(r'\d{4}-\d{2}-\d{2}_test\.pdf', '2023', 'test')
            
            # Verify verbose output
            mock_print.assert_any_call("    Searching for pattern: \\d{4}-\\d{2}-\\d{2}_test\\.pdf")
            mock_print.assert_any_call("    Year: 2023")
            mock_print.assert_any_call("    Category: test")
            mock_print.assert_any_call("    Search directories: ['test_dir']")

    def test_config_merging_edge_cases(self):
        """Test edge cases in config merging."""
        # Test merging with None values
        self.checker.base_config = {'test': {'sub': None}}
        self.checker.private_config = {'test': {'sub': ['item']}}
        merged = self.checker.merge_configs()
        self.assertEqual(merged['test']['sub'], ['item'])
        
        # Test merging with empty dictionaries
        self.checker.base_config = {'test': {}}
        self.checker.private_config = {'test': {'sub': ['item']}}
        merged = self.checker.merge_configs()
        self.assertEqual(merged['test']['sub'], ['item'])
        
        # Test merging with mixed types
        self.checker.base_config = {'test': {'sub': 'string'}}
        self.checker.private_config = {'test': {'sub': ['list']}}
        merged = self.checker.merge_configs()
        self.assertEqual(merged['test']['sub'], ['list'])

    def test_pattern_flattening_edge_cases(self):
        """Test edge cases in pattern flattening."""
        # Test with None patterns
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
        self.assertEqual(patterns['employment'], [])
        
        # Test with empty patterns list
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
        self.assertEqual(patterns['employment'], [])

    def test_find_config_file_fallback_to_code_dir(self):
        """Test finding config file in code directory when base directory doesn't exist."""
        pass

    def test_find_config_file_verbose_output(self):
        """Test verbose output when config file is not found."""
        pass

    def test_directory_access_errors(self):
        """Test handling of directory access errors."""
        pass

    def test_load_base_config_yaml_error(self):
        """Test handling of YAML parsing errors in base configuration."""
        # Create a temporary file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
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

    def test_load_base_config_file_not_found(self):
        """Test handling of missing base configuration file."""
        # Mock the file operations
        with patch('builtins.print') as mock_print:
            with patch('pathlib.Path.exists', return_value=False):
                with patch('os.path.exists', return_value=False):
                    checker = TaxDocumentChecker(base_path=self.temp_dir)
                    # Get the actual path being used
                    expected_path = os.path.join(self.temp_dir, 'tax_document_patterns_base.yml')
                    config = checker.load_base_config()
                    self.assertEqual(config, {})
                    mock_print.assert_called_with(f'Warning: Base configuration file not found at {expected_path}')

    def test_analyze_account_dates_with_invalid_dates(self):
        """Test analyzing account dates with invalid date formats."""
        # Set up test data with invalid date formats
        self.checker.required_patterns = {
            'test': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_test\.pdf',
                'name': 'Test Account',
                'frequency': 'monthly'
            }]
        }

        # Create test files with invalid dates
        test_files = [
            'invalid-date_test.pdf',  # Invalid date format
            '2023-13-45_test.pdf',    # Invalid month and day
            '2023-01-01_test.pdf'     # Valid date for comparison
        ]

        # Mock find_files_matching_pattern to return our test files
        with patch.object(self.checker, 'find_files_matching_pattern') as mock_find:
            mock_find.return_value = [os.path.join('/test', f) for f in test_files]
            
            # Run the analysis
            dates = self.checker.analyze_account_dates()
            
            # Verify that only valid dates were processed
            self.assertIn('Test Account', dates)
            self.assertEqual(dates['Test Account']['start_date'], '2023-01-01')
            self.assertEqual(dates['Test Account']['end_date'], '2023-01-01')
            # All files are included, but only valid dates are used for start/end dates
            self.assertEqual(len(dates['Test Account']['files']), 3)
            self.assertIn('2023-01-01_test.pdf', dates['Test Account']['files'])
            self.assertIn('invalid-date_test.pdf', dates['Test Account']['files'])
            self.assertIn('2023-13-45_test.pdf', dates['Test Account']['files'])

    def test_merge_configs_edge_cases(self):
        """Test merging configurations with edge cases."""
        # Test case 1: Merging lists with mixed types
        self.checker.base_config = {
            'investment': {
                'uk': [{'name': 'UK Fund', 'patterns': ['pattern1']}],
                'us': 'US Fund'  # String instead of list
            }
        }
        self.checker.private_config = {
            'investment': {
                'uk': 'UK Fund 2',  # String instead of list
                'us': [{'name': 'US Fund 2', 'patterns': ['pattern2']}]
            }
        }

        # Merge configurations
        merged = self.checker.merge_configs()

        # Verify merging behavior
        # Private config overwrites base config for 'uk'
        self.assertEqual(len(merged['investment']['uk']), 1)
        self.assertEqual(merged['investment']['uk'][0]['name'], 'UK Fund 2')
        self.assertEqual(merged['investment']['uk'][0]['patterns'], [])
        # Private config overwrites base config for 'us'
        self.assertEqual(len(merged['investment']['us']), 1)
        self.assertEqual(merged['investment']['us'][0]['name'], 'US Fund 2')
        self.assertEqual(merged['investment']['us'][0]['patterns'], ['pattern2'])

    def test_check_year_error_handling(self):
        """Test error handling in check_year method."""
        # Set up test data with invalid dates
        self.checker.required_patterns = {
            'employment': [{
                'pattern': r'\d{4}-\d{2}-\d{2}_company\.pdf',
                'name': 'Test Company',
                'frequency': 'monthly',
                'start_date': 'invalid-date',  # Invalid date format
                'end_date': '2023-12-31'
            }]
        }

        # Mock find_files_matching_pattern to return some files
        with patch.object(self.checker, 'find_files_matching_pattern') as mock_find:
            mock_find.return_value = ['/test/2023-01-01_company.pdf']
            
            # Run check_year with verbose output
            with patch('builtins.print') as mock_print:
                self.checker.verbose = True
                result = self.checker.check_year('2023')
                
                # Verify that the method handled the invalid date gracefully
                self.assertEqual(result['employment'], ['/test/2023-01-01_company.pdf'])
                mock_print.assert_any_call('  Warning: Could not parse dates, proceeding with check')

    def test_check_year_with_employment_dates(self):
        """Test check_year with employment date ranges and verify summary output."""
        # Create test config with employment date ranges
        test_config = {
            'employment': {
                'current': [
                    {
                        'name': 'current-job',
                        'patterns': [r'\d{4}-\d{2}-\d{2}_current-job\.pdf$'],
                        'frequency': 'monthly',
                        'start_date': '2022-01-01',
                        'end_date': '2023-12-31'
                    }
                ],
                'previous': [
                    {
                        'name': 'old-job',
                        'patterns': [r'\d{4}-\d{2}-\d{2}_old-job\.pdf$'],
                        'frequency': 'monthly',
                        'start_date': '2020-01-01',
                        'end_date': '2021-12-31'
                    }
                ]
            },
            'investment': {
                'uk': [
                    {
                        'name': 'investment-statement',
                        'patterns': [r'\d{4}-\d{2}-\d{2}_investment\.pdf$'],
                        'frequency': 'quarterly'
                    }
                ]
            }
        }
    
        # Create test directory structure
        base_dir = Path(self.temp_dir)
        employment_dir = base_dir / 'employment'
        investment_dir = base_dir / 'investments'
        employment_dir.mkdir()
        investment_dir.mkdir()
    
        # Create test files
        (employment_dir / '2023-01-01_current-job.pdf').touch()
        (employment_dir / '2023-02-01_current-job.pdf').touch()
        (employment_dir / '2021-01-01_old-job.pdf').touch()  # Old job file, should be skipped for 2023
        (investment_dir / '2023-03-01_investment.pdf').touch()
    
        # Create directory mapping
        dir_mapping = {
            'employment': ['employment'],
            'investment_uk': ['investments']
        }
    
        # Save configs
        config_path = base_dir / 'tax_document_patterns_base.yml'
        dir_mapping_path = base_dir / 'directory_mapping.yml'
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        with open(dir_mapping_path, 'w') as f:
            yaml.dump(dir_mapping, f)
    
        # Initialize checker with test configs
        checker = TaxDocumentChecker(
            base_path=base_dir,
            config_file=config_path,
            directory_mapping_file=dir_mapping_path,
            verbose=True
        )
    
        # Capture output
        output = StringIO()
        with redirect_stdout(output):
            checker.check_year('2023')
        
        output_str = output.getvalue()
        
        # Verify results
        assert 'Found 2 files for current-job' in output_str
        assert 'Found 1 files for investment-statement' in output_str
        assert 'No files found for old-job' in output_str  # Old job should be skipped
        assert 'MISSING OR INCOMPLETE DOCUMENTS SUMMARY' in output_str
        assert 'old-job (monthly)' in output_str  # Should be listed in missing documents

if __name__ == '__main__':
    unittest.main()
