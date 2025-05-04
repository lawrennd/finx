# Common Workflows for finx

This guide covers frequent use cases and workflows for the finx library to help you get the most out of your financial document management.

## Daily/Weekly Financial Document Management

### Adding New Documents

When you receive a new financial document (e.g., a payslip, bank statement), follow these steps:

1. Save the document with the correct naming format:
   ```
   YYYY-MM-DD_entity-name.pdf
   ```
   
   For example:
   ```
   2023-05-15_barclays-bank.pdf
   ```

2. Place the document in the appropriate directory structure:
   ```
   /payslips/2023/2023-05-15_current-employer.pdf
   /banking/uk/2023/2023-05-15_barclays-bank.pdf
   ```

3. Verify the document is recognized:
   ```bash
   finx tax status --year 2023
   ```

### Quick Status Check

Quickly see what documents you have and what you're missing:

```bash
# For the current year
finx tax status

# For a specific year
finx tax status --year 2022

# With more detailed output
finx tax status --verbose
```

### Finding Missing Documents

Generate a list of documents you're missing:

```bash
# Text output
finx tax missing

# JSON output (for processing with other tools)
finx tax missing --format json

# Export to CSV for spreadsheet tracking
finx tax missing --format csv --output missing_docs.csv
```

## Monthly Financial Reconciliation

### End-of-Month Checklist

1. Ensure all monthly documents are present:
   ```bash
   finx tax status --month 2023-05
   ```

2. Check for new entities that need to be added:
   ```bash
   finx entities check
   ```

3. Update any document dates if needed:
   ```bash
   finx tax update-dates
   ```

## Annual Tasks

### Year-End Tax Preparation

1. Ensure all documents for the tax year are present:
   ```bash
   finx tax status --year 2022 --format text
   ```

2. Create an archive of tax documents:
   ```bash
   finx tax zip --year 2022 --output tax_documents_2022.zip
   ```

3. Generate a summary of missing documents to follow up on:
   ```bash
   finx tax missing --year 2022 --output missing_tax_docs.csv --format csv
   ```

## Managing Entities

### Adding a New Financial Entity

When you start a relationship with a new financial entity:

1. Add it to your entities file (`finx_entities.yml`):

   ```yaml
   entities:
     - id: "new-investment-platform"
       name: "New Investment Platform Ltd"
       type: "investment"
       url: "https://new-investment.example.com"
       contact:
         email: "support@new-investment.example.com"
         phone: "+44 123 456 7890"
   ```

2. Add corresponding configuration to your private config file:

   ```yaml
   investment:
     uk:
       - id: "new-investment-platform-statement"
         entity_id: "new-investment-platform"
         name: "New Investment Platform"
         patterns: ["new-investment-platform"]
   ```

3. Verify the entity is correctly set up:

   ```bash
   finx entities validate
   ```

### Updating Entity Information

When an entity changes its contact details:

1. Edit the entity in your entities file:

   ```yaml
   - id: "existing-bank"
     name: "Existing Bank"
     type: "bank"
     url: "https://updated-url.example.com"  # Updated URL
     contact:
       email: "new-support@existing-bank.com"  # New email
       phone: "+44 987 654 3210"  # Updated phone
   ```

2. List all your entities to verify the update:

   ```bash
   finx entities list --format json
   
   # Or filter by type
   finx entities list --type bank
   ```

## Managing Employment Changes

### Adding a New Employer

When you start a new job:

1. Add the employer to your entities file:

   ```yaml
   - id: "new-employer"
     name: "New Employer Ltd"
     type: "employer"
     url: "https://new-employer.example.com"
     contact:
       email: "hr@new-employer.example.com"
   ```

2. Add the employment pattern to your config:

   ```yaml
   employment:
     - id: "new-employer-payslip"
       entity_id: "new-employer"
       name: "NEW_EMPLOYER"
       patterns: ["new-employer"]
       frequency: "monthly"
       start_date: "2023-05-01"
   ```

### Ending Employment

When you leave a job:

1. Update your configuration file to add an end date:

   ```yaml
   employment:
     - id: "previous-employer-payslip"
       entity_id: "previous-employer"
       name: "PREVIOUS_EMPLOYER"
       patterns: ["previous-employer"]
       frequency: "monthly"
       start_date: "2020-01-01"
       end_date: "2023-04-30"  # Add the end date
   ```

2. Verify the change:

   ```bash
   finx tax status --year 2023
   ```

## Configuration Management

### Updating Configuration After File Reorganization

If you reorganize your document directory structure:

1. Update the directory mapping in `directory_mapping.yml`:

   ```yaml
   directory_mapping:
     employment: ["employment/payslips"]  # Updated path
     bank_uk: ["finance/banking/uk"]      # Updated path
     bank_us: ["finance/banking/us"]      # Updated path
     investment_uk: ["finance/investments/uk"]  # Updated path
     investment_us: ["finance/investments/us"]  # Updated path
     additional: ["finance/tax/us", "finance/tax/uk"]  # Multiple paths
   ```

2. Test the new mappings:

   ```bash
   finx tax status
   ```

### Troubleshooting Missing Files

If files aren't being detected correctly:

1. Run with verbose output to see more details:

   ```bash
   finx tax status --verbose
   ```

2. Check the patterns in your configuration against your filenames:

   ```bash
   # Example filename: 2023-05-15_barclays-bank.pdf
   # Corresponding pattern should be: "barclays-bank"
   ```

3. Update patterns if needed:

   ```yaml
   bank:
     uk:
       - id: "barclays-bank-statement"
         entity_id: "barclays-bank"
         name: "Barclays Bank"
         patterns: ["barclays-bank", "barclays_bank"]  # Multiple patterns for flexibility
   ```

## Advanced Features

### Custom Output Formats

Generate output in different formats for integration with other tools:

```bash
# JSON output
finx tax status --format json --output status.json

# CSV output
finx entities list --format csv --output entities.csv
```

### Automating Common Tasks

Create shell scripts for frequent workflows:

```bash
#!/bin/bash
# monthly_check.sh

# Check status
finx tax status --month $(date +"%Y-%m")

# List missing documents
finx tax missing --month $(date +"%Y-%m") --format csv --output missing_$(date +"%Y-%m").csv

# Validate entities
finx entities validate
```

Make the script executable and run it:

```bash
chmod +x monthly_check.sh
./monthly_check.sh
``` 