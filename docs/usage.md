# Usage Guide

This document explains how to use the Tax Document Checker tool.

## Command Line Usage

### Basic Commands

1. Check all available tax years:
   ```
   tax-assistant
   ```

2. Check a specific tax year:
   ```
   tax-assistant --year 2023
   ```

3. Update the YAML configuration with inferred dates:
   ```
   tax-assistant --update-dates
   ```

4. List missing files:
   ```
   tax-assistant --list-missing
   ```

5. Output results in JSON format:
   ```
   tax-assistant --format json
   ```

6. Output results in CSV format:
   ```
   tax-assistant --format csv
   ```

7. Check compliance without listing files:
   ```
   tax-assistant --no-list
   ```

8. Enable console output for logging:
   ```
   tax-assistant --console-output
   ```

9. Specify a custom log file:
   ```
   tax-assistant --log-file custom.log
   ```

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--year` | Specific year to check (e.g., 2023) |
| `--update-dates` | Update YAML with inferred dates |
| `--base-path` | Base path for tax documents (default: current directory) |
| `--verbose`, `-v` | Enable verbose output for debugging |
| `--log-file` | Path to log file (default: tax_document_checker.log) |
| `--console-output` | Enable logging output to console |
| `--no-list` | Skip file listing and only check compliance |
| `--format` | Output format for file listing (choices: text, json, csv, default: text) |
| `--list-missing` | List missing files |

## Configuration

The tool uses three YAML configuration files:

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

The tool will merge both configurations at runtime, with private patterns taking precedence over base patterns when there are conflicts.

## Output Interpretation

The script provides output in the following format:

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
tax-documents/
├── UK-payslips/
│   ├── 2023/
│   │   ├── 2023-01-01_company-name.pdf
│   │   └── ...
│   └── 2022/
│       └── ...
├── US-investments/
│   ├── 2023/
│   │   └── ...
│   └── 2022/
│       └── ...
├── UK-investments/
│   └── ...
├── UK-savings/
│   └── ...
├── US-savings/
│   └── ...
├── US-tax/
│   └── ...
└── UK-tax/
    └── ...
```

## File Naming Convention

Files should follow this naming convention:
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
poetry run pytest --cov=tax_document_checker
```

### Test Data Management

The project uses Python's `tempfile` module for managing test data. This ensures:
- Clean test environments for each test run
- Automatic cleanup of test files
- Isolation between test cases
- No interference with actual tax documents

Example of using tempfile in tests:
```python
import tempfile
import os

def test_document_processing():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files in temp_dir
        test_file = os.path.join(temp_dir, "test_doc.pdf")
        # Run tests
        # Files are automatically cleaned up after the test
```

For more detailed testing guidelines and best practices, refer to the [Testing Guidelines](testing_guidelines.mdc).

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
   - Run the script with the `--update-dates` flag
   - Check that your files have dates in the correct format
   - Verify that the private YAML file is writable

4. **Configuration issues**
   - Ensure both base and private YAML files exist
   - Check that the YAML syntax is correct in both files
   - Verify that patterns in private config match your actual file naming

### Debugging

For more detailed output, you can use the `--verbose` flag:

```bash
tax-assistant --verbose
```

Or enable console output for logging:

```bash
tax-assistant --console-output
```

## Advanced Usage

### Customizing Document Patterns

You can customize the document patterns in both YAML files:

- Base patterns (tax_document_patterns_base.yml):
  - Standard document types (P60, 1099, etc.)
  - Common frequencies
  - Generic patterns

- Private patterns (tax_document_patterns_private.yml):
  - Account-specific names and identifiers
  - Start and end dates
  - Custom patterns for specific institutions

### Adding New Document Types

To add a new document type:

1. Add the generic pattern to tax_document_patterns_base.yml
2. Add account-specific information to tax_document_patterns_private.yml
3. Create the appropriate directory structure
4. Run the script to verify the new document type is recognized

### Automating Document Checks

You can automate document checks by:

1. Creating a shell script to run the checker periodically
2. Setting up a cron job to run the script at specific intervals
3. Integrating the script into your document management workflow
