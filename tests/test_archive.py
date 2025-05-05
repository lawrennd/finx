import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import zipfile
from pathlib import Path
from unittest import TestCase
from finx.archive import check_missing_files, create_zip_archive, create_password_protected_zip

class TestArchive(TestCase):
    def setUp(self):
        """Set up common test fixtures."""
        # Mock Path.stat() to return fake file stats
        self.stat_mock = MagicMock()
        self.stat_mock.st_size = 1024 * 1024  # 1MB
        self.stat_mock.st_mtime = 1678900000  # Some timestamp
        self.path_stat_patcher = patch('pathlib.Path.stat', return_value=self.stat_mock)
        self.path_stat_patcher.start()
        
        # Mock os.path.getsize to return 1MB
        self.getsize_patcher = patch('os.path.getsize', return_value=1024 * 1024)
        self.getsize_patcher.start()
        
        # Mock os.path.relpath to return a simplified path
        self.relpath_patcher = patch('os.path.relpath', return_value='test/file.pdf')
        self.relpath_patcher.start()

        # Mock getpass to avoid waiting for input
        self.getpass_patcher = patch('finx.archive.getpass', return_value='test_password')
        self.getpass_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.path_stat_patcher.stop()
        self.getsize_patcher.stop()
        self.relpath_patcher.stop()
        self.getpass_patcher.stop()

    def test_check_missing_files(self):
        """Test the check_missing_files function."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.check_year.return_value = {
            'all_found': False,
            'missing_files': [
                {
                    'path': '/test/file.pdf',
                    'name': 'test_doc',
                    'frequency': 'yearly',
                    'url': 'https://example.com'
                }
            ]
        }
        
        missing_files, all_present = check_missing_files(mock_checker)
        
        assert not all_present
        assert len(missing_files) == 1
        assert missing_files[0]['path'] == '/test/file.pdf'
        assert missing_files[0]['url'] == 'https://example.com'
        
        # Test with specific year
        missing_files, all_present = check_missing_files(mock_checker, year='2023')
        assert not all_present
        assert len(missing_files) == 1
        
        # Test with all files present
        mock_checker.check_year.return_value = {
            'all_found': True,
            'missing_files': []
        }
        missing_files, all_present = check_missing_files(mock_checker)
        assert all_present
        assert len(missing_files) == 0

    def test_create_zip_archive(self):
        """Test the create_zip_archive function."""
        with patch('finx.checker.FinancialDocumentManager') as mock_checker_class:
            mock_instance = MagicMock()
            mock_checker_class.return_value = mock_instance
            
            with patch('finx.archive.create_password_protected_zip') as mock_zip_creator:
                mock_zip_creator.return_value = True
                
                result = create_zip_archive(
                    year='2023',
                    dummy=True,
                    base_path='/test',
                    config_file='config.yml',
                    private_config_file='private.yml',
                    directory_mapping_file='mapping.yml',
                    verbose=True
                )
                
                assert result is True
                mock_checker_class.assert_called_once_with(
                    base_path='/test',
                    config_file='config.yml',
                    private_config_file='private.yml',
                    directory_mapping_file='mapping.yml',
                    verbose=True
                )
                mock_zip_creator.assert_called_once_with(
                    mock_instance,
                    year='2023',
                    output_path=None,
                    password=None,
                    dummy=True
                )

    def test_create_password_protected_zip_with_missing_files(self):
        """Test create_password_protected_zip with missing files."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.base_path = '/test'
        
        # Case where user cancels zip creation due to missing files
        with patch('finx.archive.check_missing_files') as mock_check_missing:
            mock_check_missing.return_value = (
                [{'path': '/test/file.pdf', 'name': 'test_doc', 'url': 'https://example.com'}],
                False
            )
            
            with patch('builtins.print'):
                with patch('builtins.input', return_value='n'):
                    result = create_password_protected_zip(mock_checker, dummy=False)
                    assert result is False
    
    def test_create_password_protected_zip_dummy_mode(self):
        """Test create_password_protected_zip in dummy mode."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.base_path = '/test'
        mock_checker.required_patterns = {
            'bank': [
                {
                    'pattern': 'test_pattern',
                    'name': 'test_doc'
                }
            ]
        }
        mock_checker.find_files_matching_pattern.return_value = ['/test/file.pdf']
        
        # Test in dummy mode
        with patch('finx.archive.check_missing_files') as mock_check_missing:
            mock_check_missing.return_value = ([], True)
            
            with patch('builtins.print'):
                result = create_password_protected_zip(mock_checker, dummy=True)
                assert result is True
    
    def test_create_password_protected_zip_real_mode(self):
        """Test create_password_protected_zip in real mode with password."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.base_path = '/test'
        mock_checker.required_patterns = {
            'bank': [
                {
                    'pattern': 'test_pattern',
                    'name': 'test_doc'
                }
            ]
        }
        mock_checker.find_files_matching_pattern.return_value = ['/test/file.pdf']
        
        # Create a mock pyzipper module
        mock_pyzipper = MagicMock()
        mock_aes_zipfile = MagicMock()
        mock_aes_zipfile_instance = MagicMock()
        mock_aes_zipfile.return_value.__enter__.return_value = mock_aes_zipfile_instance
        mock_pyzipper.AESZipFile = mock_aes_zipfile
        mock_pyzipper.ZIP_LZMA = 'lzma'
        mock_pyzipper.WZ_AES = 'aes'
        
        # Test in real mode with password
        with patch('finx.archive.check_missing_files') as mock_check_missing:
            mock_check_missing.return_value = ([], True)
            
            # Mock the import to return our mock module
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                      mock_pyzipper if name == 'pyzipper' else __import__(name, *args, **kwargs)):
                with patch('builtins.print'):
                    result = create_password_protected_zip(
                        mock_checker, 
                        password='test_password',
                        output_path='test.zip'
                    )
                    
                    assert result is True
                    
                    # Verify AESZipFile was called with correct parameters
                    mock_aes_zipfile.assert_called_once_with(
                        'test.zip', 'w', 
                        compression='lzma', 
                        encryption='aes'
                    )
                    # Verify password was set
                    mock_aes_zipfile_instance.setpassword.assert_called_once_with(b'test_password')
    
    def test_create_password_protected_zip_with_password_mismatch(self):
        """Test create_password_protected_zip with password mismatch."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.base_path = '/test'
        mock_checker.required_patterns = {
            'bank': [
                {
                    'pattern': 'test_pattern',
                    'name': 'test_doc'
                }
            ]
        }
        mock_checker.find_files_matching_pattern.return_value = ['/test/file.pdf']
        
        # Test password mismatch
        with patch('finx.archive.check_missing_files') as mock_check_missing:
            mock_check_missing.return_value = ([], True)
            
            with patch('builtins.print'):
                # Override the default mock with one that returns different passwords
                with patch('finx.archive.getpass') as mock_getpass:
                    mock_getpass.side_effect = ['password1', 'password2']  # Different passwords
                    
                    result = create_password_protected_zip(mock_checker)
                    
                    assert result is False
    
    def test_create_password_protected_zip_with_exception(self):
        """Test create_password_protected_zip handling exceptions."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.base_path = '/test'
        mock_checker.required_patterns = {
            'bank': [
                {
                    'pattern': 'test_pattern',
                    'name': 'test_doc'
                }
            ]
        }
        mock_checker.find_files_matching_pattern.return_value = ['/test/file.pdf']
        
        # Test exception handling
        with patch('finx.archive.check_missing_files') as mock_check_missing:
            mock_check_missing.return_value = ([], True)
            
            with patch('builtins.print'):
                with patch('zipfile.ZipFile') as mock_zipfile:
                    mock_zipfile.side_effect = Exception("Test exception")
                    
                    result = create_password_protected_zip(
                        mock_checker, 
                        password='test_password'
                    )
                    
                    assert result is False

    def test_create_password_protected_zip_without_pyzipper(self):
        """Test create_password_protected_zip without pyzipper available."""
        mock_checker = MagicMock()
        mock_checker.list_available_years.return_value = ['2023']
        mock_checker.base_path = '/test'
        mock_checker.required_patterns = {
            'bank': [
                {
                    'pattern': 'test_pattern',
                    'name': 'test_doc'
                }
            ]
        }
        mock_checker.find_files_matching_pattern.return_value = ['/test/file.pdf']
        
        # Test in real mode with password but without pyzipper
        with patch('finx.archive.check_missing_files') as mock_check_missing:
            mock_check_missing.return_value = ([], True)
            
            # Mock the import to raise ImportError for pyzipper
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                      raise_import_error(name, *args, **kwargs) if name == 'pyzipper' else __import__(name, *args, **kwargs)):
                with patch('builtins.print'):
                    with patch('zipfile.ZipFile') as mock_zipfile:
                        mock_zip_instance = MagicMock()
                        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
                        
                        result = create_password_protected_zip(
                            mock_checker, 
                            password='test_password',
                            output_path='test.zip'
                        )
                        
                        assert result is True
                        
                        # Verify normal ZipFile was used as fallback
                        mock_zipfile.assert_called_once_with('test.zip', 'w', zipfile.ZIP_DEFLATED)

# Helper function for raising ImportError
def raise_import_error(name, *args, **kwargs):
    raise ImportError(f"No module named '{name}'") 