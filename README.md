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

1. Clone this repository:
   ```
   git clone https://github.com/lawrennd/tax_document_checker.git
   cd tax_document_checker
   ```

2. Install using Poetry:
   ```
   poetry install
   ```

## Usage

### Basic Usage

To check all available tax years:
```
poetry run tax-document-checker
```

To check a specific tax year:
```
poetry run tax-document-checker --year 2023
```

To update the YAML configuration with inferred dates:
```
poetry run tax-document-checker --update-dates
```

### Configuration

The tool uses two YAML configuration files:

1. `tax_document_patterns_base.yaml` - Contains public patterns and configurations (e.g., document types like P60, 1099)
2. `tax_document_patterns_private.yaml` - Contains private account-specific information (DO NOT commit to version control)

#### Base Configuration
The base configuration defines the standard patterns and document types that are common across all users. Example:
```yaml
employment:
  patterns:
    payslip:
      base: payslip
      frequency: monthly
      annual_document_type: P60

investment:
  us:
    patterns:
      statement:
        base: statement
        frequency: quarterly
      form_1099:
        base: 1099
        frequency: yearly
```

#### Private Configuration
The private configuration contains your specific account information and patterns. This file should never be committed to version control. Example:
```yaml
employment:
  current:
  - name: "Example Company"
    patterns:
    - base: company-name
    frequency: monthly
    annual_document_type: P60
    start_date: '2020-01-01'
    end_date: null

bank:
  uk:
  - name: "Example Bank"
    account_types:
    - name: "Joint Account"
      patterns:
      - base: bank-joint
      frequency: monthly
    - name: "Personal Account"
      patterns:
      - base: bank-personal
      frequency: monthly
```

### Directory Structure
Your tax documents should be organized in the following structure:
```
tax_documents/
├── UK-payslips/
│   └── 2023/
│       ├── company-2023-01.pdf
│       ├── company-2023-02.pdf
│       └── ...
├── US-investments/
│   └── 2023/
│       ├── broker-statement-2023-Q1.pdf
│       ├── broker-statement-2023-Q2.pdf
│       └── ...
└── UK-savings/
    └── 2023/
        ├── bank-joint-2023-01.pdf
        ├── bank-joint-2023-02.pdf
        └── ...
```

## Project Structure

```
tax_document_checker/
├── README.md
├── pyproject.toml
├── poetry.lock
├── tax_document_checker/
│   ├── __init__.py
│   ├── cli.py
│   ├── checker.py
│   ├── tax_document_patterns_base.yaml
│   └── tax_document_patterns_private.yaml
├── tests/
│   ├── __init__.py
│   ├── test_checker.py
│   └── test_data/
│       ├── UK-payslips/
│       ├── US-investments/
│       └── ...
└── docs/
    ├── usage.md
    └── testing_guidelines.md
```

## Requirements

- Python 3.8+
- Poetry
- PyYAML

## Testing

The project uses pytest for testing. For comprehensive testing guidelines and best practices, see [Testing Guidelines](docs/testing_guidelines.mdc).

To run the tests:

```
poetry run pytest
```

For more verbose output:
```
poetry run pytest -v
```

To run tests with coverage report:
```
poetry run pytest --cov=tax_document_checker
```

For detailed usage instructions and examples, see [Usage Guide](docs/usage.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Note: When contributing, make sure not to commit any private information. The `tax_document_patterns_private.yaml` file is listed in `.gitignore` and should never be committed to version control.
