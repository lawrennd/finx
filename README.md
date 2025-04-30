# Finance Assistant

[![Tests](https://github.com/lawrennd/tax_document_checker/actions/workflows/tests.yml/badge.svg)](https://github.com/lawrennd/tax_document_checker/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/lawrennd/tax_document_checker/branch/main/graph/badge.svg)](https://codecov.io/gh/lawrennd/tax_document_checker)
[![Python Versions](https://img.shields.io/pypi/pyversions/tax-document-checker.svg)](https://pypi.org/project/tax-document-checker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line toolkit for managing personal finances, including tax document organization.

## Overview

`finx` provides a suite of tools to help you manage different aspects of your financial documents through a git-inspired command-line interface. Each functionality is accessible through subcommands, making it easy to extend and maintain.

## Current Features

- **Tax document management**: Track, validate, and organize your tax documents
  - Check for missing documents based on configurable patterns
  - Support for different document frequencies (monthly, quarterly, yearly)
  - Automatic date extraction from filenames
  - Validation of document completeness for specific tax years
  - Multiple output formats (text, JSON, CSV)

## Planned Features (Coming Soon)

- **Investment tracking**: Monitor investment performance across accounts
- **Net worth calculation**: Track assets and liabilities over time
- **Budget management**: Track income and expenses
- **Estate planning**: Document organization for wills and estate planning
- **Savings goals**: Track progress towards savings targets

## Installation

### Option 1: Install directly with pip
```bash
pip install git+https://github.com/lawrennd/finx.git
```

### Option 2: Install from source using Poetry (for development)
1. Clone this repository:
   ```bash
   git clone https://github.com/lawrennd/finx.git
   cd finx
   ```

2. Install using Poetry:
   ```bash
   poetry install
   ```

## Usage

Finance Assistant uses a command structure inspired by `git` with subcommands for different functionality:

### Tax Document Management

```bash
# Check tax documents for the current year
finx tax status

# Check a specific tax year
finx tax status --year 2023

# List missing documents with URLs
finx tax missing

# Create a zip file of tax documents
finx tax zip --year 2023

# Update document configuration with inferred dates
finx tax update-dates
```

### Investment Tracking (Planned)

```bash
# View investment summary
finx invest summary

# Check performance
finx invest performance --period 1y

# View asset allocation
finx invest allocation
```

### Net Worth Tracking (Planned)

```bash
# Calculate current net worth
finx networth status

# Show net worth history
finx networth history --period 5y

# Add a new asset or liability
finx networth add-asset "Home" --value 500000
```

### Budget Management (Planned)

```bash
# View current monthly budget status
finx budget status

# Add an expense
finx budget add-expense "Groceries" --amount 150.75

# Generate a budget report
finx budget report --month 2023-05
```

### Estate Planning (Planned)

```bash
# List estate documents
finx estate list

# Check for missing critical documents
finx estate verify
```

For detailed usage instructions for each command, see the [Usage Guide](docs/usage.md).

## Configuration

The tool uses YAML configuration files to separate public patterns from private account information:

- **Base Configuration**: Public patterns and configurations that can be shared
- **Private Configuration**: Account-specific information (not committed to version control)
- **Directory Mapping**: Defines where different document types are stored

See the [Usage Guide](docs/usage.md) for detailed configuration examples.

## Security Considerations

Finance Assistant is designed with privacy and security in mind:

- Private information is kept separate from base configuration
- No financial data is sent to external services
- All processing happens locally on your machine
- Sensitive files are excluded from version control by default
- Test data is included in the repository but contains no real personal or financial information
  - Test documents are empty PDFs or contain only example data
  - Real documents should be stored outside the repository
  - The `.gitignore` file is configured to exclude real documents while keeping test data

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.