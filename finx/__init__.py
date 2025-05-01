"""
Finance Assistant (Finx)

A Python utility for checking and validating tax documents based on configurable patterns and frequencies.
"""

from finx.checker import FinancialDocumentManager
from finx.archive import create_zip_archive, create_password_protected_zip

__version__ = "0.1.0"

__all__ = ['FinancialDocumentManager', 'create_zip_archive', 'create_password_protected_zip'] 
