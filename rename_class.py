#!/usr/bin/env python3

import os
import re
from pathlib import Path

def replace_in_file(file_path, old_text, new_text):
    """Replace old_text with new_text in file_path."""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Replace the class name
    new_content = content.replace(old_text, new_text)
    
    # Only write back if changes were made
    if new_content != content:
        with open(file_path, 'w') as file:
            file.write(new_content)
        return True
    return False

def main():
    # Define the search paths
    base_path = Path.cwd()
    python_files = list(base_path.glob('finx/**/*.py')) + list(base_path.glob('tests/**/*.py'))
    
    # Define replacements
    replacements = [
        ('TaxDocumentChecker', 'FinancialDocumentManager'),
        ('tax_document_checker', 'financial_document_manager'),
        ('tax-document-checker', 'financial-document-manager')
    ]
    
    print(f"Found {len(python_files)} Python files to process")
    
    # Process each file
    for file_path in python_files:
        print(f"Processing {file_path}")
        
        for old_text, new_text in replacements:
            if replace_in_file(file_path, old_text, new_text):
                print(f"  - Replaced '{old_text}' with '{new_text}'")
    
    print("\nClass rename complete!")
    print("\nNow run tests to verify the changes:")
    print("  pytest")

if __name__ == "__main__":
    main() 