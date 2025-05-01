"""
Functions for creating password-protected zip files of documents.
"""

import os
import zipfile
from pathlib import Path
from getpass import getpass

def check_missing_files(checker, year=None):
    """
    Check for missing files using the FinancialDocumentManager.
    
    Args:
        checker: FinancialDocumentManager instance
        year: Specific year to check (optional)
    
    Returns:
        tuple: (missing_files_list, all_files_present)
    """
    # Get all years to check
    years_to_check = [year] if year else checker.list_available_years()
    
    missing_files = []
    all_files_present = True
    
    for year in years_to_check:
        results = checker.check_year(year, list_missing=True)
        if not results['all_found']:
            all_files_present = False
            missing_files.extend(results.get('missing_files', []))
    
    return missing_files, all_files_present

def create_zip_archive(year=None, dummy=False, base_path=None, config_file=None, 
                       private_config_file=None, directory_mapping_file=None, 
                       output_path=None, password=None, verbose=False):
    """
    Create a zip archive of tax documents.
    
    Args:
        year (str): Specific tax year to include
        dummy (bool): If True, only simulate without creating a zip file
        base_path (str): Base path containing tax documents
        config_file (str): Path to base configuration file
        private_config_file (str): Path to private configuration file
        directory_mapping_file (str): Path to directory mapping file
        output_path (str): Path where to save the zip file
        password (str): Password for the zip file
        verbose (bool): Enable verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Import here to avoid circular imports
    from .checker import FinancialDocumentManager
    
    # Initialize the checker
    checker = FinancialDocumentManager(
        base_path=base_path,
        config_file=config_file,
        private_config_file=private_config_file,
        directory_mapping_file=directory_mapping_file,
        verbose=verbose
    )
    
    # Create the zip file using the existing function
    return create_password_protected_zip(
        checker,
        year=year,
        output_path=output_path,
        password=password,
        dummy=dummy
    )

def create_password_protected_zip(checker, year=None, output_path=None, password=None, dummy=False):
    """
    Create a password-protected zip file containing tax documents.
    
    Args:
        checker: FinancialDocumentManager instance
        year: Specific year to include (optional)
        output_path: Path where to save the zip file (optional)
        password: Password for the zip file (optional)
        dummy: If True, only simulate the process without creating a zip file (optional)
    """
    # First check for missing files
    print("\nChecking for missing tax documents...")
    missing_files, all_files_present = check_missing_files(checker, year)
    
    if missing_files:
        print("\nWARNING: The following tax documents are missing:")
        print("-" * 50)
        for file_info in missing_files:
            print(f"- {file_info['path']}")
            if file_info.get('url'):
                print(f"  Can be found at: {file_info['url']}")
        print("-" * 50)
        if not dummy:
            response = input("\nDo you want to continue creating the zip file? (y/N): ")
            if response.lower() != 'y':
                print("Zip file creation cancelled.")
                return False
    else:
        print("All required tax documents are present.")
    
    # Get all years to include
    years_to_check = [year] if year else checker.list_available_years()
    
    if not years_to_check:
        print("No tax years found in the directory.")
        return False
    
    # Collect all files to include
    files_to_zip = []
    for year in years_to_check:
        # Get all patterns from the checker
        for category, patterns in checker.required_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                name = pattern_info['name']
                
                # Find matching files
                matches = checker.find_files_matching_pattern(pattern, year=year, category=category)
                files_to_zip.extend(matches)
    
    if not files_to_zip:
        print("No files found to zip.")
        return False
    
    # Generate output path if not provided
    if not output_path:
        years_str = f"{year}" if year else f"{min(years_to_check)}-{max(years_to_check)}"
        output_path = f"tax_documents_{years_str}.zip"
    
    # Get password if not provided and not in dummy mode
    if not password and not dummy:
        password = getpass("Enter password for the zip file: ")
        confirm_password = getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match.")
            return False
    elif dummy:
        password = "dummy_password"
    
    print(f"\nFiles that would be included in {output_path}:")
    print("-" * 50)
    total_size = 0
    for file_path in files_to_zip:
        rel_path = os.path.relpath(file_path, checker.base_path)
        size = os.path.getsize(file_path)
        total_size += size
        print(f"{rel_path} ({size / (1024*1024):.2f} MB)")
    print("-" * 50)
    print(f"Total files: {len(files_to_zip)}")
    print(f"Total size: {total_size / (1024*1024):.2f} MB")
    
    if dummy:
        print("\nDummy mode: No zip file was created.")
        return True
    
    # Create the zip file
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add each file to the zip
            for file_path in files_to_zip:
                # Get the relative path for the file in the zip
                rel_path = os.path.relpath(file_path, checker.base_path)
                print(f"Adding: {rel_path}")
                zipf.write(file_path, rel_path, pwd=password.encode() if password else None)
        
        print(f"\nSuccessfully created password-protected zip file: {output_path}")
        print(f"Total files included: {len(files_to_zip)}")
        return True
    
    except Exception as e:
        print(f"Error creating zip file: {str(e)}")
        return False 