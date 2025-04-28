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
- Multiple output formats (text, JSON, CSV)
- Detailed logging with configurable verbosity

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
tax-assistant
```

To check a specific tax year:
```bash
tax-assistant --year 2023
```

To update the YAML configuration with inferred dates:
```bash
tax-assistant --update-dates
```

To specify a custom base path for tax documents:
```bash
tax-assistant --base-path /path/to/tax/documents
```

To show detailed information about configuration loading and file searching:
```bash
tax-assistantr --verbose
```

To list missing files:
```bash
tax-assistant --list-missing
```

To output results in JSON format:
```bash
tax-assistant --format json
```

To output results in CSV format:
```bash
tax-assistant --format csv
```

To check compliance without listing files:
```bash
tax-assistant --no-list
```

To enable console output for logging:
```bash
tax-assistant --console-output
```

To specify a custom log file:
```bash
tax-assistant --log-file custom.log
```

Note: If you installed using Poetry for development, prefix the commands with `poetry run`:
```bash
poetry run tax-assistant
```

## Configuration

The tool uses two YAML configuration files to separate public patterns from private account information:

### Base Configuration (tax_document_patterns_base.yml)

Contains public patterns and configurations that can be shared and version controlled:

```yaml
employment:
  patterns:
    payslip:
      base: payslip
      frequency: monthly
      annual_document_type: P60
    p45:
      base: p45
      frequency: once
    p60:
      base: p60
      frequency: yearly

investment:
  us:
    patterns:
      1099_div:
        base: 1099-div
        frequency: yearly
```

### Private Configuration (tax_document_patterns_private.yml)

Contains account-specific information and should NOT be committed to version control:

```yaml
employment:
  current:
    - name: "EXAMPLE_EMPLOYER"  # Replace with actual employer name
      patterns:
        - base: example-employer  # Replace with actual pattern
      frequency: monthly
      annual_document_type: P60
      start_date: '2020-01-01'  # Replace with actual date
      end_date: null  # null for current employment
```

### Directory Mapping (directory_mapping.yml)

Defines where different document types are stored:

```yaml
directory_mapping:
  employment: 
    - payslips
  investment_us: 
    - investments/us
  investment_uk: 
    - investments/uk
  bank_uk: 
    - banking/uk
    - UK-savings
  bank_us: 
    - banking/us
  additional: 
    - tax/us
    - tax/uk
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: File system error