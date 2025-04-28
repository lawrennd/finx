"""
Tax Document Checker

A Python utility for checking and validating tax documents based on configurable patterns and frequencies.
"""

from tax_assistant.checker import TaxDocumentChecker
from tax_assistant.archive import create_zip_archive, create_password_protected_zip

__version__ = "0.1.0"

__all__ = ['TaxDocumentChecker', 'create_zip_archive', 'create_password_protected_zip'] 
