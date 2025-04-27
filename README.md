# Tax Document Checker

[![Tests](https://github.com/lawrennd/tax_document_checker/actions/workflows/tests.yml/badge.svg)](https://github.com/lawrennd/tax_document_checker/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/lawrennd/tax_document_checker/branch/main/graph/badge.svg)](https://codecov.io/gh/lawrennd/tax_document_checker)
[![Python Versions](https://img.shields.io/pypi/pyversions/tax-document-checker.svg)](https://pypi.org/project/tax-document-checker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python utility for checking and validating tax documents based on configurable patterns and frequencies.

## Overview

This tool helps you track and validate your tax documents by checking for the presence of required files based on their expected frequency (monthly, quarterly, yearly, etc.). It supports various document types including:

- Employment documents (payslips, P60s)
- Investment documents (US and UK)
- Bank statements (US and UK)
- Additional tax documents (tax returns, FinCEN forms, etc.)

## Features

- Configurable document patterns via YAML
- Support for different document frequencies (monthly, quarterly, yearly)
- Automatic date extraction from filenames
- Validation of document completeness for specific tax years
- Support for annual summary documents (P60, 1099, etc.)
- Automatic detection of account start and end dates
- Separation of public and private configuration

## Installation

### Option 1: Install directly with pip
```bash
pip install git+https://github.com/lawrennd/tax_document_checker.git
```

Note: To install from the private repository, you need:
- Git installed on your system
- Access permissions to the repository
- Git credentials configured to access private repositories
- If using SSH, ensure your SSH key is added to your GitHub account

### Option 2: Install from source using Poetry (for development)
1. Clone this repository:
   ```bash
   git clone https://github.com/lawrennd/tax_document_checker.git
   cd tax_document_checker
   ```

2. Install using Poetry:
   ```bash
   poetry install
   ```

## Usage

### Basic Usage

To check all available tax years:
```bash
tax-document-checker
```

To check a specific tax year:
```bash
tax-document-checker --year 2023
```

To update the YAML configuration with inferred dates:
```bash
tax-document-checker --update-dates
```

To specify a custom base path for tax documents:
```bash
tax-document-checker --base-path /path/to/tax/documents
```

To show detailed information about configuration loading and file searching:
```bash
tax-document-checker --verbose
```

Note: If you installed using Poetry for development, prefix the commands with `poetry run`:
```bash
poetry run tax-document-checker
```

The tool returns the following exit codes:

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: File system error

## Additional Notes

The tool returns the following exit codes:

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: File system error