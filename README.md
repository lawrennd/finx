# Finance Assistant

[![Tests](https://github.com/lawrennd/finx/actions/workflows/tests.yml/badge.svg)](https://github.com/lawrennd/finx/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/lawrennd/finx/branch/main/graph/badge.svg)](https://codecov.io/gh/lawrennd/finx)
[![Python Versions](https://img.shields.io/pypi/pyversions/finx.svg)](https://pypi.org/project/finx/)
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

- **Entity management**: Track contact details for financial entities
  - Store contact information for accountants, banks, and other financial entities
  - Support for different entity types (accountants, banks, investment platforms, etc.)
  - Check for missing entity information in configuration files
  - Maintain addresses, URLs, and notes for each entity

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

### Entity Management

```bash
# List all entities
finx entities list

# List entities of a specific type
finx entities list --type accountant

# Check for missing entities
finx entities check

# Migrate to the dual ID system
finx entities migrate --config=your_config.yml --entities=your_entities.yml

# Validate entity references
finx entities validate --config=your_config.yml --entities=your_entities.yml
```

The tool maintains a database of financial entities and their contact details in `finx_entities.yml`. Each entity can be one of the following types:
- **accountant**: Tax and accounting services
- **bank**: Banking institutions
- **investment**: Investment platforms and brokers
- **insurance**: Insurance providers
- **legal**: Legal services
- **government**: Government agencies (HMRC, IRS, etc.)
- **employer**: Current and previous employers
- **utility**: Utility providers
- **other**: Other financial entities

The `check` command compares entities mentioned in your configuration files with those in the entities database, helping you maintain complete contact information for all your financial relationships.

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

For common workflows and practical examples, see the [Common Workflows Guide](docs/common_workflows.md).

## Configuration

The tool uses YAML configuration files to separate public patterns from private account information:

- **Base Configuration**: Public patterns and configurations that can be shared
- **Private Configuration**: Account-specific information (not committed to version control)
- **Directory Mapping**: Defines where different document types are stored
- **Entity Database**: Stores contact details for financial entities

### Dual ID System

The finance document configuration specifies two ids for all entries in configuration files:

- **id**: A unique identifier for each document type (e.g., `current-employer-payslip`)
- **entity_id**: A reference to the entity in the `finx_entities.yml` file (e.g., `current-employer`)

For guidance on migrating existing configurations to the dual ID system, see the [Migration Guide](docs/dual_id_migration.md).

Example configuration:

```yaml
employment:
  - id: "current-employer-payslip"
    entity_id: "current-employer"
    name: "CURRENT_EMPLOYER"
    patterns: ["current-employer"]
    frequency: "monthly"
    start_date: "2022-01-01"
```


### Employment Configuration

Employers are configured using start and end dates:

```yaml
employment:
  - id: "current-employer-payslip"
    entity_id: "current-employer"
    name: "CURRENT_EMPLOYER"
    patterns: ["current-employer"]
    frequency: "monthly"
    start_date: "2022-01-01"
    # No end_date means currently employed
  
  - id: "previous-employer-payslip"
    entity_id: "previous-employer"
    name: "PREVIOUS_EMPLOYER"
    patterns: ["previous-employer"]
    frequency: "monthly"
    start_date: "2018-01-01"
    end_date: "2021-12-31"
```

The tool automatically determines if an employer is current or previous based on the dates.

See the [Usage Guide](docs/usage.md) for detailed configuration examples.

## Development Roadmap

We follow a structured approach to improving the library through Code Improvement Plans (CIPs):

- [CIP-0001](cip/cip0001.md): Dual ID Implementation (Completed)
- [CIP-0002](cip/cip0002.md): Enhancing User Experience and Documentation (In Progress)

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