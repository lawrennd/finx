# Usage Guide

This document explains how to use the Finance Assistant toolkit.

## Command-Line Structure

Finance Assistant uses a Git-like command structure with subcommands for different financial management functions:

```
finx <command> <subcommand> [options]
```

Available commands:

- `tax`: Tax document management
- `entities`: Entity management
- `invest`: Investment tracking (planned)
- `networth`: Net worth calculation (planned)
- `budget`: Budget management (planned)
- `estate`: Estate planning (planned)
- `savings`: Savings goals tracking (planned)

## Tax Document Management

The `tax` command helps you organize and manage tax documents.

### Subcommands

#### status

Check tax documents for completeness.

```bash
# Check all available tax years
finx tax status

# Check a specific tax year
finx tax status --year 2023

# Verbose output with detailed information
finx tax status --verbose
```

#### missing

List missing tax documents.

```bash
# List missing documents for all years
finx tax missing

# List missing documents for a specific year
finx tax missing --year 2023

# Output in JSON format
finx tax missing --format json

# Output in CSV format
finx tax missing --format csv
```

The `--format` option is currently only implemented for the `tax missing` command and supports `text` (default), `json`, and `csv` formats.

#### zip

Create a password-protected zip archive of tax documents.

```bash
# Create a zip for the current tax year
finx tax zip

# Create a zip for a specific tax year
finx tax zip --year 2023

# Test run without creating the zip (shows what would be included)
finx tax zip --dummy
```

The `--dummy` option performs a dry run that lists all files that would be included in the archive without actually creating the zip file. This is useful for verifying the content before creating the actual archive.

#### update-dates

Update the configuration with inferred dates from filenames.

```bash
finx tax update-dates
```

### Global Options for Tax Command

| Option | Description |
|----------|-------------|
| `--year` | Specific year to check (e.g., 2023) |
| `--base-path` | Base path for tax documents (default: current directory) |
| `--verbose`, `-v` | Enable verbose output for debugging |
| `--log-file` | Path to log file (default: finx.log) |
| `--format` | Output format (choices: text, json, csv, default: text) |
| `--config-file` | Path to base configuration file |
| `--private-config-file` | Path to private configuration file |
| `--directory-mapping-file` | Path to directory mapping file |

## Entity Management

The `entities` command helps you track contact details for financial entities.

### Subcommands

#### list

List stored entities and their contact details.

```bash
# List all entities
finx entities list

# List entities of a specific type
finx entities list --type accountant

# Output in JSON format
finx entities list --format json

# Output in CSV format
finx entities list --format csv
```

#### check

Check for missing entity information in configuration files.

```bash
# Check for missing entities
finx entities check

# Check for missing entities and output in JSON format
finx entities check --format json

# Check for missing entities and output in CSV format 
finx entities check --format csv
```

### Entity Types

The tool supports the following entity types:
- **accountant**: Tax and accounting services
- **bank**: Banking institutions
- **investment**: Investment platforms and brokers
- **insurance**: Insurance providers
- **legal**: Legal services
- **government**: Government agencies (HMRC, IRS, etc.)
- **employer**: Current and previous employers
- **utility**: Utility providers
- **other**: Other financial entities

### Global Options for Entity Command

| Option | Description |
|----------|-------------|
| `--type`, `-t` | Filter entities by type (e.g., accountant, bank) |
| `--format` | Output format (choices: text, json, csv, default: text) |
| `--config-file` | Path to entity configuration file (planned) |

## Investment Tracking (Planned)

The `invest` command will help you track and analyze your investments. This feature is currently planned but not yet implemented.

### Planned Subcommands

#### summary

Display a summary of all investments.

```bash
finx invest summary
```

#### performance

Check performance of investments.

```bash
# Check performance for all time periods
finx invest performance

# Check performance for specific period
finx invest performance --period 1y
```

#### allocation

View asset allocation.

```bash
finx invest allocation
```

## Net Worth Tracking (Planned)

The `networth` command will help you track your overall financial position. This feature is currently planned but not yet implemented.

### Planned Subcommands

#### status

Show current net worth.

```bash
finx networth status
```

#### history

Show net worth changes over time.

```bash
# Show all history
finx networth history

# Show history for a specific period
finx networth history --period 5y
```

#### add-asset

Add a new asset.

```bash
finx networth add-asset "Home" --value 500000 --type real-estate
```

#### add-liability

Add a new liability.

```bash
finx networth add-liability "Mortgage" --value 300000 --type loan
```

## Budget Management (Planned)

The `budget` command will help you track income and expenses. This feature is currently planned but not yet implemented.

### Planned Subcommands

#### status

Show current budget status.

```bash
finx budget status
```

#### add-income

Add income transaction.

```bash
finx budget add-income "Salary" --amount 5000 --category employment
```

#### add-expense

Add expense transaction.

```bash
finx budget add-expense "Groceries" --amount 150.75 --category food
```

#### report

Generate budget reports.

```bash
# Report for current month
finx budget report

# Report for specific month
finx budget report --month 2023-05
```

## Estate Planning (Planned)

The `estate` command will help you organize documents for wills and estate planning. This feature is currently planned but not yet implemented.

### Planned Subcommands

#### list

List estate planning documents.

```bash
finx estate list
```

#### verify

Check for missing critical documents.

```bash
finx estate verify
```

## Savings Goals (Planned)

The `savings` command will help you track progress towards savings goals. This feature is currently planned but not yet implemented.

### Planned Subcommands

#### list

List all savings goals.

```bash
finx savings list
```

#### add

Add a new savings goal.

```bash
finx savings add "New Car" --target 25000 --deadline 2025-06
```

#### update

Update progress on a savings goal.

```bash
finx savings update "New Car" --current 5000
```

## Configuration

The tool uses four YAML configuration files:

### Base Configuration (finx_base.yml)

Contains public patterns and configurations that can be shared and version controlled:

```yaml
tax:
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

### Private Configuration (finx_private.yml)

Contains account-specific information and should NOT be committed to version control:

```yaml
# Employment has a flat structure with status determined automatically from dates
employment:
  - name: "EXAMPLE_EMPLOYER"  # Replace with actual employer name
    patterns:
      - base: example-employer  # Replace with actual pattern
    frequency: monthly
    annual_document_type: P60
    start_date: '2020-01-01'  # Replace with actual date
    # No end_date means current employment

  - name: "PREVIOUS_EMPLOYER"
    patterns:
      - base: previous-employer
    frequency: monthly
    annual_document_type: P60
    start_date: '2018-01-01'
    end_date: '2019-12-31'  # End date indicates previous employment

invest:
  accounts:
    - name: "EXAMPLE_BROKERAGE"
      type: "taxable"
      institution: "Example Broker"
      login_url: "https://example-broker.com/login"
```

Employment status (current or previous) is automatically determined from dates:
- An employer with no `end_date` or `end_date: null` is considered currently active
- An employer with a specific `end_date` in the past is considered a previous employer
- For the year being checked, employers with date ranges outside that year are skipped

### Directory Mapping (directory_mapping.yml)

Defines where different document types are stored:

```yaml
directory_mapping:
  tax:
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
  
  estate:
    documents:
      - estate/wills
      - estate/power_of_attorney
```

### Entity Database (finx_entities.yml)

Stores contact details for financial entities:
```yaml
entities:
  - name: "Example Accountants Ltd"
    type: "accountant"
    contact:
      primary: "John Smith"
      email: "john@exampleaccountants.com"
    address:
      street: "123 Accounting Street"
      city: "London"
      postcode: "EC1A 1AA"
      country: "UK"
```

## Output Interpretation (Tax Documents)

The script provides output in the following format for tax document checking:

```
Checking documents for tax year 2023
==================================================

EMPLOYMENT:
✓ Found 12/12 files for Company Name (monthly)
  - 2023-01-01_company-name.pdf
  - 2023-02-01_company-name.pdf
  ...

INVESTMENT_US:
✓ Found 1/1 files for Investment Company (yearly)
  - 2023-12-31_investment-company.pdf

BANK_UK:
⚠ Found 11/12 files for Bank Name - savings-account (monthly)
  - 2023-01-01_bank-name_savings.pdf
  - 2023-02-01_bank-name_savings.pdf
  ...

MISSING OR INCOMPLETE DOCUMENTS SUMMARY:
==================================================

BANK_UK:
- Bank Name - savings-account (monthly)
```

### Output Symbols

- ✓: All required documents found
- ⚠: Some documents found but not all
- ✗: No documents found
- ⨯: Account closed before this year or not started yet

## Directory Structure

The script expects your tax documents to be organized in the following directory structure:

```
finance/
├── tax/
│   ├── UK-payslips/
│   │   ├── 2023/
│   │   │   ├── 2023-01-01_company-name.pdf
│   │   │   └── ...
│   │   └── 2022/
│   │       └── ...
│   ├── US-investments/
│   │   └── ...
│   ├── UK-investments/
│   │   └── ...
│   └── ...
├── investments/
│   ├── statements/
│   │   └── ...
│   └── performance/
│       └── ...
├── networth/
│   └── ...
└── estate/
    ├── wills/
    │   └── ...
    └── power_of_attorney/
        └── ...
```

## File Naming Convention

For tax documents, files should follow this naming convention:
```
YYYY-MM-DD_base-name_identifier.pdf
```

Example:
```
2023-01-01_company-name.pdf
2023-12-31_bank-name_savings.pdf
```

## Testing

For comprehensive testing guidelines and best practices, see [Testing Guidelines](testing_guidelines.mdc).

### Running Tests

Basic test execution:
```bash
poetry run pytest
```

With verbose output:
```bash
poetry run pytest -v
```

With coverage report:
```bash
poetry run pytest --cov=tax_assistant
```

## Troubleshooting

### Common Issues

1. **No files found for a category**
   - Check that your files are in the correct directory
   - Verify that your file names match the expected pattern
   - Ensure both base and private YAML configurations have the correct patterns defined

2. **Incorrect file count**
   - Verify that the frequency in the YAML matches your actual document frequency
   - Check that all files for the year are present
   - Ensure files are named with the correct date format

3. **Account dates not updating**
   - Run the script with the `tax update-dates` command
   - Check that your files have dates in the correct format
   - Verify that the private YAML file is writable

4. **Configuration issues**
   - Ensure both base and private YAML files exist
   - Check that the YAML syntax is correct in both files
   - Verify that patterns in private config match your actual file naming

### Debugging

For more detailed output, you can use the `--verbose` flag:

```bash
finx tax status --verbose
```

## Security Considerations

- Private financial information should only be stored in the private configuration file
- The private configuration file should NOT be committed to version control
- Password protection is used for zip files containing tax documents
- No data is sent to external servers; all processing is done locally





