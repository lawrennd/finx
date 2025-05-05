# Migrating to the Dual ID System

This guide explains how to migrate your existing finx configuration files to use the new dual ID system introduced in version 0.2.0.

## Understanding the Dual ID System

In previous versions, each entry in your configuration files used a single `id` field to identify both the entity (e.g., a bank) and the document type (e.g., bank statements). The new system separates these concerns:

- **entity_id**: References an entity in your `finx_entities.yml` file
- **id**: A unique identifier for each document type

This separation provides several benefits:
- Better organization of entities across different document types
- Easier reuse of entity information
- Improved validation of configuration files
- Clearer separation between entities and documents

## Automatic Migration

The easiest way to migrate is using the built-in migration tool:

```bash
# Basic usage
finx entities migrate --config=your_config.yml --entities=your_entities.yml

# To preview changes without applying them
finx entities migrate --config=your_config.yml --entities=your_entities.yml --dry-run

# To automatically add missing entities to your entities file
finx entities migrate --config=your_config.yml --entities=your_entities.yml --add-missing-entities
```

### What the Migration Tool Does

1. For each entry in your configuration files:
   - If both `entity_id` and `id` exist, no changes are made
   - If only `id` exists, it's used as the `entity_id` and a new document-specific `id` is generated
   - If both are missing, they're generated based on the entry's name

2. For each entity referenced:
   - Verifies it exists in your entities file
   - Optionally adds missing entities to your entities file

## Manual Migration

If you prefer to migrate manually, here's how to update each section:

### Employment Section

**Before:**
```yaml
employment:
  - id: example-employer
    name: "Example Current Employer"
    frequency: "monthly"
    patterns: ["example-current-employer"]
    start_date: "2022-01-01"
```

**After:**
```yaml
employment:
  - id: example-employer-payslip
    entity_id: example-employer
    name: "Example Current Employer"
    frequency: "monthly"
    patterns: ["example-current-employer"]
    start_date: "2022-01-01"
```

### Bank Section

**Before:**
```yaml
bank:
  uk:
    - id: example-bank
      name: "Example Bank"
      account_types:
        - id: example-bank-current
          name: "Current Account"
          patterns: [{"base": "example-bank", "account_type": "current"}]
```

**After:**
```yaml
bank:
  uk:
    - id: example-bank-statement
      entity_id: example-bank
      name: "Example Bank"
      account_types:
        - id: example-bank-current-statement
          entity_id: example-bank
          name: "Current Account"
          patterns: [{"base": "example-bank", "account_type": "current"}]
```

### Investment Section

**Before:**
```yaml
investment:
  uk:
    - id: example-investment
      name: "Example Investment Platform"
      patterns: ["example-investment"]
```

**After:**
```yaml
investment:
  uk:
    - id: example-investment-statement
      entity_id: example-investment
      name: "Example Investment Platform"
      patterns: ["example-investment"]
```

### Additional Section

**Before:**
```yaml
additional:
  - id: example-tax-return
    name: "Example Tax Return"
    patterns: ["example-tax-return"]
```

**After:**
```yaml
additional:
  - id: example-tax-return-doc
    entity_id: example-tax-return
    name: "Example Tax Return"
    patterns: ["example-tax-return"]
```

## Validation

After migration, you should validate your configuration to ensure all entity references are correct:

```bash
finx entities validate --config=your_config.yml --entities=your_entities.yml
```

This will check that:
1. All entities referenced in your config file exist in your entities file
2. All entries have both `id` and `entity_id` fields
3. There are no duplicate IDs

## Best Practices for Dual IDs

When creating new entries or updating existing ones:

1. **Use descriptive entity_ids** that reflect the entity's name
   - Good: `barclays-bank`
   - Avoid: `bank1` or `bb`

2. **Use descriptive document-specific ids** that include both the entity and document type
   - Good: `barclays-bank-statement` or `acme-corp-payslip`
   - Avoid: `statement1` or `doc-123`

3. **Maintain consistency** across similar document types
   - For payslips: `employer-name-payslip`
   - For bank statements: `bank-name-statement`
   - For investment documents: `platform-name-statement`

4. **Ensure uniqueness** of all IDs across your configuration

## Troubleshooting

If you encounter issues during migration:

### Common Issues

1. **Duplicate IDs**: The migration tool may generate IDs that already exist
   - Solution: Manually edit the duplicates to use unique IDs

2. **Missing entities**: The tool identifies entity references that don't exist in your entities file
   - Solution: Run with `--add-missing-entities` or manually add the missing entities

3. **Validation errors after migration**: Some references may not be correctly updated
   - Solution: Run the validation tool to identify issues and fix them manually

### Getting Help

If you need further assistance:
- Open an issue on the GitHub repository
- Check the troubleshooting section in the main documentation
- Run commands with the `--verbose` flag for more detailed output 