# Usage Guide

This document explains how to use the Finance Assistant toolkit.

## Command-Line Structure

Finance Assistant uses a Git-like command structure with subcommands for different financial management functions:

```
finx <command> <subcommand> [options]
```

Available commands:

- `tax`: Tax document management
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

#### zip

Create a password-protected zip archive of tax documents.

```bash
# Create a zip for the current tax year
finx tax zip

# Create a zip for a specific tax year
finx tax zip --year 2023

# Test run without creating the zip
finx tax zip --dummy
```

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
| `--log-file` | Path to log file (default: finance_assistant.log) |
| `--format` | Output format (choices: text, json, csv, default: text) |
| `--config-file` | Path to base configuration file |
| `--private-config-file` | Path to private configuration file |
| `--directory-mapping-file` | Path to directory mapping file |

## Investment Tracking (Planned)

The `invest` command will help you track and analyze your investments.

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

The `networth` command will help you track your overall financial position.

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

The `budget` command will help you track income and expenses.

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

The `estate` command will help you organize documents for wills and estate planning.

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

The `savings` command will help you track progress towards savings goals.

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

The tool uses three YAML configuration files:

### Base Configuration (finance_assistant_base.yml)

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

### Private Configuration (finance_assistant_private.yml)

Contains account-specific information and should NOT be committed to version control:

```yaml
tax:
  employment:
    current:
      - name: "EXAMPLE_EMPLOYER"  # Replace with actual employer name
        patterns:
          - base: example-employer  # Replace with actual pattern
        frequency: monthly
        annual_document_type: P60
        start_date: '2020-01-01'  # Replace with actual date
        end_date: null  # null for current employment

invest:
  accounts:
    - name: "EXAMPLE_BROKERAGE"
      type: "taxable"
      institution: "Example Broker"
      login_url: "https://example-broker.com/login"
```

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
poetry run pytest --cov=finance_assistant
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
